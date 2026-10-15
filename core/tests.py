from io import StringIO

from django.core.management import call_command
from django.test import Client, TestCase

from accounts.models import User
from articles.models import Article, Comment, TopicSuggestion
from finances.models import Transaction


class DemoInstallationTests(TestCase):
    def test_demo_installation_can_be_repeated_without_duplicates_or_password_reset(self):
        commands = ('seed_demo', 'seed_test_accounts', 'seed_community', 'seed_articles')
        for command in commands:
            call_command(command, stdout=StringIO())
        self.assertEqual(User.objects.filter(email__endswith='@finhom.local').count(), 7)
        self.assertEqual(Article.objects.count(), 7)
        self.assertEqual(Comment.objects.count(), 17)
        self.assertEqual(TopicSuggestion.objects.count(), 5)
        passwords = dict(User.objects.values_list('email', 'password'))
        transaction_count = Transaction.objects.count()
        for command in commands:
            call_command(command, stdout=StringIO())
        self.assertEqual(dict(User.objects.values_list('email', 'password')), passwords)
        self.assertEqual(Transaction.objects.count(), transaction_count)
        self.assertEqual(Comment.objects.count(), 17)

        for user in User.objects.filter(email__endswith='@finhom.local'):
            self.client.force_login(user)
            for url in ('/articles/', '/analytics/', '/finances/planning/', '/finances/goals/', '/loans/', '/accounts/profile/'):
                with self.subTest(email=user.email, url=url):
                    self.assertEqual(self.client.get(url).status_code, 200)

    def test_financial_write_requires_csrf_token(self):
        user = User.objects.create_user(email='csrf@example.com', first_name='Тест')
        user.profile.onboarding_completed = True
        user.profile.save()
        client = Client(enforce_csrf_checks=True)
        client.force_login(user)
        response = client.post('/finances/transactions/add/', {})
        self.assertEqual(response.status_code, 403)
