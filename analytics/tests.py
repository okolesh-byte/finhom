from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Profile, User
from finances.models import Category, Transaction
from .services import build_summary
from loans.models import Loan, LoanPayment
from finances.models import RecurringPayment


class SummaryTests(TestCase):
    def test_summary_uses_age_and_builds_available_forecasts(self):
        user = User.objects.create_user(email='forecast@example.com', first_name='Анна', password='StrongPassword2026!')
        Profile.objects.update_or_create(user=user, defaults={'birth_date': date(1990, 1, 1), 'expected_income': Decimal('60000')})
        income = Category.objects.create(name='Доход тест', kind=Category.INCOME, owner=user)
        expense = Category.objects.create(name='Расход тест', kind=Category.EXPENSE, owner=user)
        for month in range(1, 7):
            Transaction.objects.create(user=user, category=income, kind=Category.INCOME, amount=Decimal('60000'), operation_date=date(2026, month, 10))
            Transaction.objects.create(user=user, category=expense, kind=Category.EXPENSE, amount=Decimal('30000'), operation_date=date(2026, month, 12))

        summary = build_summary(user, today=date(2026, 7, 1))
        self.assertEqual(summary['reserve_months'], 6)
        self.assertEqual([row['months'] for row in summary['forecast_rows']], [3, 6])
        self.assertEqual(summary['recommended_reserve'], Decimal('180000'))


class AnalyticsAuditTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='audit@example.com', first_name='Тест')
        self.user.profile.expected_income = Decimal('60000')
        self.user.profile.onboarding_completed = True
        self.user.profile.save()
        self.today = timezone.localdate()
        self.income = Category.objects.get(name='Зарплата', is_system=True)
        self.expense = Category.objects.get(name='Продукты', is_system=True)

    def operation(self, kind, amount, category=None, operation_date=None):
        return Transaction.objects.create(
            user=self.user, kind=kind, amount=Decimal(amount),
            category=category or (self.income if kind == Category.INCOME else self.expense),
            operation_date=operation_date or self.today,
        )

    def loan(self, **changes):
        data = dict(
            user=self.user, name='Кредит', bank='Банк', original_amount=100000,
            current_balance=50000, annual_rate=12, monthly_payment=5000,
            start_date='2026-01-01', end_date='2027-12-31', payment_day=15, months_left=12,
        )
        data.update(changes)
        return Loan.objects.create(**data)

    def test_future_operations_do_not_change_balance(self):
        self.operation(Category.INCOME, '10000')
        self.operation(Category.EXPENSE, '9000', operation_date=self.today.replace(year=self.today.year + 1))
        summary = build_summary(self.user)
        self.assertEqual(summary['balance'], Decimal('10000'))
        self.assertEqual(summary['expenses'], Decimal('0'))

    def test_credit_expense_is_not_subtracted_twice_in_month_forecast(self):
        self.operation(Category.INCOME, '60000')
        self.operation(Category.EXPENSE, '5000', Category.objects.get(name='Кредиты', is_system=True))
        self.loan()
        self.assertEqual(build_summary(self.user)['expected_balance'], Decimal('55000'))

    def test_confirmed_overdue_payment_raises_high_risk(self):
        self.operation(Category.INCOME, '60000')
        LoanPayment.objects.create(
            loan=self.loan(), due_date=self.today, planned_amount=5000, status=LoanPayment.OVERDUE,
        )
        self.assertEqual(build_summary(self.user)['risk'][0], 'high')

    def test_chart_category_cannot_inject_script(self):
        payload = '</script><script>alert(1)</script>'
        category = Category.objects.create(name=payload, kind=Category.EXPENSE, owner=self.user)
        self.operation(Category.EXPENSE, '100', category)
        self.client.force_login(self.user)
        response = self.client.get(reverse('analytics:dashboard'))
        self.assertNotContains(response, payload)
        self.assertContains(response, 'application/json')

    def test_empty_account_is_not_marked_financially_stable(self):
        summary = build_summary(self.user)
        self.assertEqual(summary['risk'][0], 'unknown')
        self.assertEqual(summary['forecast_rows'], [])

    def test_no_income_with_credit_is_high_risk(self):
        self.user.profile.expected_income = 0
        self.user.profile.save()
        self.loan()
        summary = build_summary(self.user)
        self.assertIsNone(summary['debt_ratio'])
        self.assertEqual(summary['risk'][0], 'high')

    def test_recurring_expense_is_included_in_month_forecast(self):
        self.operation(Category.INCOME, '60000')
        RecurringPayment.objects.create(user=self.user, category=self.expense, name='Оплата',
            amount=3000, day=31, start_date=self.today.replace(day=1))
        self.assertEqual(build_summary(self.user)['expected_balance'], Decimal('57000'))

    def test_loan_is_not_charged_beyond_its_remaining_term(self):
        self.operation(Category.INCOME, '60000')
        self.loan(months_left=1)
        forecast = build_summary(self.user)['forecast_rows'][0]
        self.assertEqual(forecast['months'], 3)
        self.assertEqual(forecast['balance'], Decimal('235000'))
