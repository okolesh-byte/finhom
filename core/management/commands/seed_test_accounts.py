import secrets
from calendar import monthrange
from datetime import date
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from accounts.models import Profile, User
from finances.models import Category, MonthlyBudget, RecurringPayment, SavingsGoal, Transaction
from loans.models import Loan, LoanPayment


TEST_PROFILES = [
    {'email': 'student@finhom.local', 'name': 'Максим', 'birth': (2007, 3, 12),
     'income': 38000, 'expenses': (6500, 2400, 2800),
     'loan': ('Ноутбук для учёбы', 85000, '18.5', 4300, 20), 'goal': ('Курсы программирования', 60000, 12000)},
    {'email': 'specialist@finhom.local', 'name': 'Анна', 'birth': (2001, 8, 24),
     'income': 72000, 'expenses': (14500, 5200, 7600),
     'loan': ('Потребительский кредит', 240000, '19.9', 11800, 24), 'goal': ('Путешествие', 150000, 47000)},
    {'email': 'family@finhom.local', 'name': 'Дмитрий', 'birth': (1993, 11, 6),
     'income': 110000, 'expenses': (26000, 8900, 13500),
     'loan': ('Автокредит', 920000, '16.7', 45500, 28), 'goal': ('Семейный резерв', 330000, 96000)},
    {'email': 'risk@finhom.local', 'name': 'Сергей', 'birth': (1984, 2, 17),
     'income': 70000, 'expenses': (19500, 6800, 10500),
     'loan': ('Кредит на ремонт', 680000, '24.5', 39000, 25), 'goal': ('Финансовая подушка', 210000, 15000)},
    {'email': 'stable@finhom.local', 'name': 'Елена', 'birth': (1970, 6, 30),
     'income': 155000, 'expenses': (22000, 7400, 12000),
     'loan': ('Ипотечный кредит', 1450000, '9.8', 23800, 72), 'goal': ('Резерв на 6 месяцев', 600000, 410000)},
]


def month_date(today, offset, day=1):
    year, month = divmod(today.year * 12 + today.month - 1 + offset, 12)
    return date(year, month + 1, min(day, monthrange(year, month + 1)[1]))


class Command(BaseCommand):
    help = 'Создаёт пять локальных финансовых профилей, сохраняя пароли существующих аккаунтов'

    @transaction.atomic
    def handle(self, *args, **options):
        today = timezone.localdate()
        categories = {category.name: category for category in Category.objects.filter(is_system=True)}
        required = {'Зарплата', 'Продукты', 'Транспорт', 'Развлечения', 'Связь'}
        if not required.issubset(categories):
            raise CommandError('Сначала примените миграции с системными категориями.')
        for index, data in enumerate(TEST_PROFILES, start=1):
            user, created = User.objects.get_or_create(email=data['email'], defaults={'first_name': data['name']})
            if created:
                password = secrets.token_urlsafe(12)
                user.set_password(password)
                user.save(update_fields=['password'])
                self.stdout.write(f'{user.email} / {password}')
            Profile.objects.update_or_create(user=user, defaults={
                'birth_date': date(*data['birth']), 'expected_income': data['income'], 'payday': 10,
                'reserve_target': data['income'] * 3, 'onboarding_completed': True,
            })
            for months_back in range(6):
                factor = Decimal('1') + Decimal(months_back % 3 - 1) * Decimal('0.04')
                for name, kind, amount, day in [
                    ('Зарплата', Category.INCOME, data['income'], 10),
                    *[(name, Category.EXPENSE, amount, 14 + i * 3)
                      for i, (name, amount) in enumerate(zip(('Продукты', 'Транспорт', 'Развлечения'), data['expenses']))],
                ]:
                    operation_date = min(month_date(today, -months_back, day), today)
                    note = f'Тест: {"доход" if kind == Category.INCOME else name.lower()} {months_back}'
                    Transaction.objects.update_or_create(user=user, category=categories[name], note=note,
                        defaults={'operation_date': operation_date, 'kind': kind, 'amount': Decimal(amount) * factor})
            MonthlyBudget.objects.update_or_create(user=user, category=categories['Продукты'], month=today.replace(day=1),
                defaults={'limit': data['expenses'][0] * 2})
            RecurringPayment.objects.update_or_create(user=user, name='Связь и интернет', defaults={
                'category': categories['Связь'], 'amount': 900 + index * 150, 'day': 5,
                'start_date': month_date(today, -5), 'is_active': True,
            })
            name, target, current = data['goal']
            SavingsGoal.objects.update_or_create(user=user, name=name, defaults={
                'target_amount': target, 'current_amount': current, 'target_date': month_date(today, 8, 25),
            })
            name, amount, rate, payment, months = data['loan']
            loan, _ = Loan.objects.update_or_create(user=user, name=name, defaults={
                'bank': 'Учебный банк', 'original_amount': amount, 'current_balance': Decimal(amount) * Decimal('0.72'),
                'annual_rate': Decimal(rate), 'monthly_payment': payment, 'start_date': month_date(today, -10, 15),
                'end_date': month_date(today, months, 15), 'payment_day': 15, 'months_left': months, 'is_active': True,
            })
            for months_back in range(3, -1, -1):
                due = month_date(today, -months_back, 15)
                status, actual_date, actual_amount = LoanPayment.PLANNED, None, None
                if months_back:
                    status, actual_date, actual_amount = LoanPayment.EARLY, month_date(today, -months_back, 13), payment
                if months_back == 1 and data['email'] == 'risk@finhom.local':
                    status, actual_date, actual_amount = LoanPayment.OVERDUE, None, None
                LoanPayment.objects.update_or_create(loan=loan, due_date=due, defaults={
                    'planned_amount': payment, 'actual_date': actual_date, 'actual_amount': actual_amount, 'status': status,
                })
        self.stdout.write(self.style.SUCCESS('Пять профилей готовы. Пароли существующих аккаунтов сохранены.'))
