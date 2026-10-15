from django.core.management.base import BaseCommand, CommandError

from accounts.models import User
from articles.models import Article, Comment, TopicSuggestion


COMMUNITY_DATA = [
    {
        'email': 'student@finhom.local',
        'comment': 'Начал записывать траты и увидел, сколько денег уходило на мелкие покупки.',
        'comment_status': Comment.PENDING,
        'topic': 'Как студенту собрать финансовую подушку',
        'description': 'Хочу понятный план накоплений при небольшой зарплате и подработке.',
        'topic_status': TopicSuggestion.PENDING,
        'note': '',
    },
    {
        'email': 'specialist@finhom.local',
        'comment': 'Правило бюджета помогло мне заранее отложить деньги на путешествие.',
        'comment_status': Comment.PUBLISHED,
        'topic': 'Как распределить первую зарплату',
        'description': 'Статья для тех, кто недавно начал работать и хочет не потратить всё сразу.',
        'topic_status': TopicSuggestion.ACCEPTED,
        'note': 'Хорошая тема, добавили её в план публикаций.',
    },
    {
        'email': 'family@finhom.local',
        'comment': 'Хотелось бы больше примеров именно для семейного бюджета.',
        'comment_status': Comment.REJECTED,
        'topic': 'Семейный бюджет без конфликтов',
        'description': 'Как договориться о совместных целях и обязательных расходах.',
        'topic_status': TopicSuggestion.PENDING,
        'note': '',
    },
    {
        'email': 'risk@finhom.local',
        'comment': 'После расчёта долговой нагрузки понял, что новый кредит сейчас брать нельзя.',
        'comment_status': Comment.PENDING,
        'topic': 'Что делать при большой кредитной нагрузке',
        'description': 'Нужна пошаговая статья о том, какие долги закрывать первыми.',
        'topic_status': TopicSuggestion.ACCEPTED,
        'note': 'Тема важная, материал уже готовится.',
    },
    {
        'email': 'stable@finhom.local',
        'comment': 'Полезно видеть цель и прогресс накоплений в одном месте.',
        'comment_status': Comment.PUBLISHED,
        'topic': 'Обзор сложных инвестиционных стратегий',
        'description': 'Предлагаю разобрать активную торговлю и сложные биржевые инструменты.',
        'topic_status': TopicSuggestion.REJECTED,
        'note': 'Пока Finhom посвящён личному бюджету, долгам и безопасным привычкам.',
    },
]


class Command(BaseCommand):
    help = 'Добавляет комментарии и предложения тем пяти тестовым аккаунтам'

    def handle(self, *args, **options):
        article = Article.objects.filter(is_published=True).order_by('pk').first()
        if not article:
            raise CommandError('Сначала создайте и опубликуйте хотя бы одну статью.')

        for item in COMMUNITY_DATA:
            try:
                user = User.objects.get(email=item['email'])
            except User.DoesNotExist as error:
                raise CommandError(f'Не найден тестовый аккаунт {item["email"]}.') from error

            Comment.objects.get_or_create(
                article=article,
                author=user,
                text=item['comment'],
                defaults={
                    'status': item['comment_status'],
                    'moderator_note': item['note'] if item['comment_status'] == Comment.REJECTED else '',
                },
            )
            TopicSuggestion.objects.get_or_create(
                user=user,
                title=item['topic'],
                defaults={
                    'description': item['description'],
                    'status': item['topic_status'],
                    'moderator_note': item['note'],
                },
            )

        self.stdout.write(self.style.SUCCESS('Добавлено 5 комментариев и 5 предложений тем.'))
