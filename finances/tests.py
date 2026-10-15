from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from accounts.models import Profile, User
from .models import Category, MonthlyBudget, Transaction
from .models import SavingsGoal
from .forms import TransactionForm, RecurringPaymentForm


class TransactionAccessTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(email='owner@example.com', first_name='Владелец', password='StrongPassword2026!')
        self.other = User.objects.create_user(email='other@example.com', first_name='Другой', password='StrongPassword2026!')
        Profile.objects.update_or_create(user=self.owner, defaults={'birth_date': date(2000, 1, 1), 'onboarding_completed': True})
        Profile.objects.update_or_create(user=self.other, defaults={'birth_date': date(2000, 1, 1), 'onboarding_completed': True})
        self.category = Category.objects.create(name='Тест', kind=Category.EXPENSE, owner=self.owner)
        self.transaction = Transaction.objects.create(user=self.owner, category=self.category, kind=Category.EXPENSE, amount=Decimal('500'), operation_date=date.today())

    def test_user_cannot_edit_another_users_transaction(self):
        self.client.force_login(self.other)
        response = self.client.get(reverse('finances:transaction_edit', args=[self.transaction.pk]))
        self.assertEqual(response.status_code, 404)

    def test_saving_same_budget_updates_limit(self):
        self.client.force_login(self.owner)
        data = {
            'action': 'budget', 'budget-category': self.category.pk,
            'budget-month': date.today().strftime('%Y-%m'), 'budget-limit': '10000',
        }
        self.client.post(reverse('finances:planning'), data)
        data['budget-limit'] = '15000'
        self.client.post(reverse('finances:planning'), data)
        self.assertEqual(MonthlyBudget.objects.filter(user=self.owner, category=self.category).count(), 1)
        self.assertEqual(MonthlyBudget.objects.get(user=self.owner, category=self.category).limit, Decimal('15000'))

    def test_csv_export_contains_only_current_users_transactions(self):
        Transaction.objects.create(
            user=self.other, category=Category.objects.create(name='Чужая', kind=Category.EXPENSE, owner=self.other),
            kind=Category.EXPENSE, amount=Decimal('999'), operation_date=date.today(), note='Чужая операция',
        )
        self.client.force_login(self.owner)
        response = self.client.get(reverse('finances:transaction_export'))
        content = response.content.decode('utf-8-sig')
        self.assertEqual(response.status_code, 200)
        self.assertIn('500', content)
        self.assertNotIn('Чужая операция', content)

    def test_goal_created_already_funded_is_completed(self):
        self.client.force_login(self.owner)
        self.client.post(reverse('finances:goals'), {
            'name': 'Готовая цель', 'target_amount': '1000', 'current_amount': '1000',
        })
        self.assertEqual(SavingsGoal.objects.get(user=self.owner).status, SavingsGoal.COMPLETED)

    def test_csv_does_not_export_executable_formulas(self):
        self.transaction.note = '=HYPERLINK("https://example.com")'
        self.transaction.save()
        self.client.force_login(self.owner)
        response = self.client.get(reverse('finances:transaction_export'))
        import csv
        import io
        rows = list(csv.reader(io.StringIO(response.content.decode('utf-8-sig')), delimiter=';'))
        self.assertEqual(rows[1][-1], "'" + self.transaction.note)

    def test_transaction_cannot_use_another_users_category(self):
        form = TransactionForm(user=self.other, data={
            'kind': Category.EXPENSE, 'category': self.category.pk,
            'amount': '100', 'operation_date': date.today().isoformat(),
        })
        self.assertFalse(form.is_valid())
        self.assertIn('category', form.errors)

    def test_date_input_preserves_existing_date(self):
        form = TransactionForm(user=self.owner, instance=self.transaction)
        self.assertIn(f'value="{self.transaction.operation_date.isoformat()}"', str(form['operation_date']))

    def test_recurring_payment_accepts_only_expense_category(self):
        income = Category.objects.get(name='Зарплата', is_system=True)
        form = RecurringPaymentForm(user=self.owner, data={
            'name': 'Неверный платёж', 'category': income.pk, 'amount': '100',
            'day': '10', 'start_date': date.today().isoformat(),
        })
        self.assertFalse(form.is_valid())
        self.assertIn('category', form.errors)
