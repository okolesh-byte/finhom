from datetime import date, timedelta
from decimal import Decimal
import secrets

from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import Profile, User
from articles.models import Article, ArticleCategory
from finances.models import Category, MonthlyBudget, SavingsGoal, Transaction
from loans.models import Loan, LoanPayment


class Command(BaseCommand):
    help = 'Создаёт локальные демонстрационные данные Finhom'

    def handle(self, *args, **options):
        admin, created = User.objects.get_or_create(
            email='admin@finhom.local',
            defaults={'first_name': 'Администратор', 'is_staff': True, 'is_superuser': True},
        )
        if created:
            admin_password = secrets.token_urlsafe(14)
            admin.set_password(admin_password)
            admin.save()
        Profile.objects.update_or_create(user=admin, defaults={'birth_date': date(1990, 1, 1), 'onboarding_completed': True})

        user, created = User.objects.get_or_create(email='demo@finhom.local', defaults={'first_name': 'Алексей'})
        if created:
            user_password = secrets.token_urlsafe(14)
            user.set_password(user_password)
            user.save()
        Profile.objects.update_or_create(
            user=user,
            defaults={'birth_date': date(2003, 5, 18), 'expected_income': Decimal('72000'), 'payday': 10, 'reserve_target': Decimal('150000'), 'onboarding_completed': True},
        )

        categories = {item.name: item for item in Category.objects.filter(is_system=True)}
        today = date.today()
        examples = [
            ('Зарплата', 'income', '72000', today.replace(day=10), 'Зарплата за месяц'),
            ('Продукты', 'expense', '12480', today, 'Покупки на неделю'),
            ('Транспорт', 'expense', '3650', today - timedelta(days=2), 'Проезд'),
            ('Жильё', 'expense', '18500', today - timedelta(days=4), 'Аренда и коммунальные услуги'),
            ('Развлечения', 'expense', '4900', today - timedelta(days=5), 'Выходные'),
        ]
        for category_name, kind, amount, operation_date, note in examples:
            Transaction.objects.get_or_create(user=user, category=categories[category_name], kind=kind, amount=Decimal(amount), operation_date=operation_date, note=note)

        MonthlyBudget.objects.get_or_create(user=user, category=categories['Продукты'], month=today.replace(day=1), defaults={'limit': Decimal('20000')})
        SavingsGoal.objects.get_or_create(user=user, name='Путешествие', defaults={'target_amount': Decimal('120000'), 'current_amount': Decimal('38000'), 'target_date': today + timedelta(days=240)})

        loan, _ = Loan.objects.get_or_create(
            user=user,
            name='Потребительский кредит',
            defaults={
                'bank': 'Демо Банк', 'original_amount': Decimal('300000'), 'current_balance': Decimal('214500'),
                'annual_rate': Decimal('18.9'), 'monthly_payment': Decimal('12400'),
                'start_date': today - timedelta(days=300), 'end_date': today + timedelta(days=600),
                'payment_day': 15, 'months_left': 20,
            },
        )
        LoanPayment.objects.get_or_create(loan=loan, due_date=today.replace(day=15), defaults={'planned_amount': loan.monthly_payment, 'status': LoanPayment.PLANNED})

        category = ArticleCategory.objects.get(slug='budget')
        Article.objects.get_or_create(
            title='Как составить бюджет, которого реально придерживаться',
            defaults={
                'category': category, 'author': admin,
                'summary': 'Простой способ распределить доходы, обязательные платежи и деньги на цели.',
                'body': 'Начните не с жёстких ограничений, а с наблюдения. Записывайте расходы в течение месяца и объединяйте их по категориям.\n\nСначала отложите деньги на обязательные платежи, затем определите сумму для накопительной цели. Оставшуюся часть распределите между повседневными категориями.\n\nПроверяйте бюджет раз в неделю. Если одна категория быстро заканчивается, уменьшите менее важные траты, а не отказывайтесь от плана полностью.',
                'published_at': timezone.now(), 'is_published': True,
            },
        )
        self.stdout.write(self.style.SUCCESS('Демонстрационные данные готовы.'))
        if 'user_password' in locals():
            self.stdout.write(f'Пользователь: demo@finhom.local / {user_password}')
        if 'admin_password' in locals():
            self.stdout.write(f'Администратор: admin@finhom.local / {admin_password}')
