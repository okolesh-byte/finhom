from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from accounts.models import Profile, User
from .forms import EarlyRepaymentForm, LoanForm, LoanPaymentForm
from .models import Loan, LoanPayment
from .services import calculate_early_repayment
from django.core.exceptions import ValidationError


class LoanFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='loan@example.com', first_name='Иван', password='StrongPassword2026!')
        Profile.objects.update_or_create(
            user=self.user,
            defaults={'birth_date': date(1995, 1, 1), 'onboarding_completed': True},
        )
        self.loan = Loan.objects.create(
            user=self.user, name='Тестовый кредит', bank='Тест Банк',
            original_amount=Decimal('100000'), current_balance=Decimal('80000'), annual_rate=Decimal('15'),
            monthly_payment=Decimal('5000'), start_date=date.today() - timedelta(days=30),
            end_date=date.today() + timedelta(days=700), payment_day=15, months_left=20,
        )

    def test_loan_form_rejects_invalid_balance_and_dates(self):
        form = LoanForm(data={
            'name': 'Ошибка', 'bank': 'Банк', 'original_amount': '100000', 'current_balance': '120000',
            'annual_rate': '10', 'monthly_payment': '5000', 'start_date': '2026-10-10',
            'end_date': '2026-10-01', 'payment_day': '15', 'months_left': '10', 'is_active': 'on',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('current_balance', form.errors)
        self.assertIn('end_date', form.errors)

    def test_payment_does_not_guess_new_bank_balance(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('loans:add_payment', args=[self.loan.pk]), {
            'due_date': date.today().isoformat(), 'planned_amount': '5000',
            'actual_date': date.today().isoformat(), 'actual_amount': '5000',
            'status': LoanPayment.ON_TIME, 'note': '',
        })
        self.assertRedirects(response, reverse('loans:detail', args=[self.loan.pk]))
        self.loan.refresh_from_db()
        self.assertEqual(self.loan.current_balance, Decimal('80000'))

    def test_early_repayment_cannot_exceed_balance(self):
        form = EarlyRepaymentForm(
            data={'amount': '90000', 'repayment_date': date.today().isoformat(), 'strategy': 'term'},
            loan=self.loan,
        )
        self.assertFalse(form.is_valid())
        self.assertIn('amount', form.errors)

    def test_full_early_repayment_has_zero_months_and_payment(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('loans:early_repayment', args=[self.loan.pk]), {
            'amount': '80000', 'repayment_date': date.today().isoformat(), 'strategy': 'term',
        }, follow=True)
        result = self.loan.early_repayments.get()
        self.assertEqual(result.estimated_months, 0)
        self.assertEqual(result.estimated_payment, Decimal('0'))
        self.assertContains(response, 'Последний расчёт')

    def test_negative_actual_payment_is_rejected(self):
        form = LoanPaymentForm(data={
            'due_date': date.today().isoformat(), 'planned_amount': '5000',
            'actual_date': date.today().isoformat(), 'actual_amount': '-100', 'status': LoanPayment.ON_TIME,
        })
        self.assertFalse(form.is_valid())

    def test_future_actual_payment_is_rejected(self):
        form = LoanPaymentForm(data={
            'due_date': date.today().isoformat(), 'planned_amount': '5000',
            'actual_date': (date.today() + timedelta(days=10)).isoformat(),
            'actual_amount': '5000', 'status': LoanPayment.ON_TIME,
        })
        self.assertFalse(form.is_valid())

    def test_zero_rate_repayment_uses_simple_division(self):
        self.loan.annual_rate = Decimal('0')
        result = calculate_early_repayment(self.loan, Decimal('30000'), 'payment')
        self.assertEqual(result['estimated_payment'], Decimal('2500'))
        self.assertEqual(result['estimated_months'], 20)

    def test_unpayable_interest_is_an_error_not_a_false_term(self):
        self.loan.annual_rate = Decimal('120')
        self.loan.monthly_payment = Decimal('100')
        with self.assertRaises(ValidationError):
            calculate_early_repayment(self.loan, Decimal('1000'), 'term')

    def test_duplicate_scheduled_date_is_a_form_error(self):
        LoanPayment.objects.create(loan=self.loan, due_date=date.today(), planned_amount=5000)
        self.client.force_login(self.user)
        response = self.client.post(reverse('loans:add_payment', args=[self.loan.pk]), {
            'due_date': date.today().isoformat(), 'planned_amount': '5000', 'status': LoanPayment.PLANNED,
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('due_date', response.context['form'].errors)
        self.assertEqual(self.loan.payments.count(), 1)

    def test_payment_date_is_not_replaced_with_date_of_entry(self):
        self.client.force_login(self.user)
        paid = date.today() - timedelta(days=4)
        due = date.today() - timedelta(days=2)
        self.client.post(reverse('loans:add_payment', args=[self.loan.pk]), {
            'due_date': due.isoformat(), 'planned_amount': '5000', 'actual_date': paid.isoformat(),
            'actual_amount': '5000', 'status': LoanPayment.ON_TIME,
        })
        payment = self.loan.payments.get()
        self.assertEqual(payment.actual_date, paid)
        self.assertEqual(payment.due_date, due)
        self.assertEqual(payment.status, LoanPayment.EARLY)
