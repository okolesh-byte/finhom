from django.test import TestCase
from django.contrib.auth.models import Permission
from django.urls import reverse
from django.utils import timezone

from accounts.models import User

from .models import Article, ArticleCategory, Comment, TopicSuggestion


class CommunityFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='reader@example.com', password='test-pass', first_name='Ирина')
        self.staff = User.objects.create_user(
            email='moderator@example.com', password='test-pass', first_name='Модератор', is_staff=True
        )
        self.staff.user_permissions.add(*Permission.objects.filter(
            content_type__app_label='articles', codename__in=['change_comment', 'change_topicsuggestion', 'change_article'],
        ))
        category = ArticleCategory.objects.create(name='Тестовая категория', slug='test-category')
        self.article = Article.objects.create(
            category=category,
            author=self.staff,
            title='Тестовая статья',
            summary='Краткое описание',
            body='Текст статьи',
            is_published=True,
            published_at=timezone.now(),
        )

    def test_comment_stays_hidden_until_moderation(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('articles:detail', args=[self.article.pk]), {'text': 'Полезный материал'})
        self.assertRedirects(response, reverse('articles:detail', args=[self.article.pk]))
        comment = Comment.objects.get()
        self.assertEqual(comment.status, Comment.PENDING)
        response = self.client.get(reverse('articles:detail', args=[self.article.pk]))
        self.assertFalse(response.context['comments'].exists())
        self.assertEqual(response.context['own_comments'].get(), comment)

    def test_staff_can_edit_and_publish_comment(self):
        comment = Comment.objects.create(article=self.article, author=self.user, text='Черновой текст')
        self.client.force_login(self.staff)
        response = self.client.post(
            reverse('articles:moderate_comment', args=[comment.pk]),
            {'text': 'Исправленный текст', 'status': Comment.PUBLISHED, 'moderator_note': ''},
        )
        self.assertRedirects(response, reverse('articles:moderation'))
        comment.refresh_from_db()
        self.assertEqual(comment.text, 'Исправленный текст')
        self.assertEqual(comment.status, Comment.PUBLISHED)

        self.client.force_login(self.user)
        response = self.client.get(reverse('articles:detail', args=[self.article.pk]))
        self.assertContains(response, 'Исправленный текст')

    def test_user_can_suggest_topic_and_see_status(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('articles:suggest'),
            {'title': 'Как вести бюджет', 'description': 'Нужен простой пример бюджета на месяц.'},
        )
        self.assertRedirects(response, reverse('articles:suggest'))
        suggestion = TopicSuggestion.objects.get()
        self.assertEqual(suggestion.status, TopicSuggestion.PENDING)
        response = self.client.get(reverse('articles:suggest'))
        self.assertContains(response, 'Как вести бюджет')
        self.assertContains(response, 'На рассмотрении')

    def test_staff_can_accept_topic_with_answer(self):
        suggestion = TopicSuggestion.objects.create(
            user=self.user,
            title='Финансовая подушка',
            description='Как накопить резерв.',
        )
        self.client.force_login(self.staff)
        response = self.client.post(
            reverse('articles:moderate_suggestion', args=[suggestion.pk]),
            {'status': TopicSuggestion.ACCEPTED, 'moderator_note': 'Добавили в план.'},
        )
        self.assertRedirects(response, reverse('articles:moderation'))
        suggestion.refresh_from_db()
        self.assertEqual(suggestion.status, TopicSuggestion.ACCEPTED)
        self.assertEqual(suggestion.moderator_note, 'Добавили в план.')

    def test_regular_user_cannot_open_moderation(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('articles:moderation'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/login/', response.url)

    def test_staff_without_model_permissions_cannot_moderate(self):
        staff = User.objects.create_user(email='limited@example.com', first_name='Сотрудник', is_staff=True)
        self.client.force_login(staff)
        self.assertEqual(self.client.get(reverse('articles:moderation')).status_code, 403)
        comment = Comment.objects.create(article=self.article, author=self.user, text='Текст')
        response = self.client.post(reverse('articles:moderate_comment', args=[comment.pk]), {
            'text': 'Изменён', 'status': Comment.PUBLISHED, 'moderator_note': '',
        })
        self.assertEqual(response.status_code, 403)
        comment.refresh_from_db()
        self.assertEqual(comment.status, Comment.PENDING)

    def test_comment_moderator_cannot_publish_articles(self):
        staff = User.objects.create_user(email='comments@example.com', first_name='Модератор', is_staff=True)
        staff.user_permissions.add(Permission.objects.get(content_type__app_label='articles', codename='change_comment'))
        self.client.force_login(staff)
        self.assertEqual(self.client.get(reverse('articles:moderation')).status_code, 200)
        response = self.client.post(reverse('articles:toggle_article', args=[self.article.pk]))
        self.assertEqual(response.status_code, 403)
