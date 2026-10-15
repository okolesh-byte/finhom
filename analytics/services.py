from calendar import monthrange
from datetime import date
from decimal import Decimal

from django.db.models import Min, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone

from finances.models import Category, Transaction
from loans.models import LoanPayment


def month_after(source, offset):
    year, month = divmod(source.year * 12 + source.month - 1 + offset, 12)
    return date(year, month + 1, 1)


def build_summary(user, today=None):
    today = today or timezone.localdate()
    profile = user.profile
    profile.refresh_from_db()
    month_start = today.replace(day=1)
    month_end = today.replace(day=monthrange(today.year, today.month)[1])
    transactions = Transaction.objects.filter(user=user, operation_date__lte=today)
    current = transactions.filter(operation_date__gte=month_start)
    income = current.filter(kind=Category.INCOME).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    expenses = current.filter(kind=Category.EXPENSE).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    all_income = transactions.filter(kind=Category.INCOME).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    all_expenses = transactions.filter(kind=Category.EXPENSE).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    data_months = transactions.order_by().annotate(month=TruncMonth('operation_date')).values('month').distinct().count()
    loans = list(user.loans.filter(is_active=True, current_balance__gt=0, start_date__lte=today))
    debt_payment = sum((loan.monthly_payment for loan in loans), Decimal('0'))

    credit_categories = set(Category.objects.filter(is_system=True, name='Кредиты').values_list('pk', flat=True))
    first_date = transactions.aggregate(first=Min('operation_date'))['first']
    complete_months = (today.year - first_date.year) * 12 + today.month - first_date.month if first_date else 0
    history = transactions.filter(operation_date__lt=month_start) if complete_months else transactions
    months_count = max(complete_months, 1)
    average_income = (history.filter(kind=Category.INCOME).aggregate(total=Sum('amount'))['total'] or Decimal('0')) / months_count
    average_by_category = {
        row['category_id']: row['total'] / months_count
        for row in history.filter(kind=Category.EXPENSE).exclude(category_id__in=credit_categories)
        .order_by().values('category_id').annotate(total=Sum('amount'))
    }
    current_by_category = {
        row['category_id']: row['total']
        for row in current.filter(kind=Category.EXPENSE).exclude(category_id__in=credit_categories)
        .order_by().values('category_id').annotate(total=Sum('amount'))
    }
    recurring = list(user.recurring_payments.filter(is_active=True))

    def mandatory_by_category(month):
        amounts = {}
        for payment in recurring:
            due_date = month.replace(day=min(payment.day, monthrange(month.year, month.month)[1]))
            if payment.start_date <= due_date:
                amounts[payment.category_id] = amounts.get(payment.category_id, Decimal('0')) + payment.amount
        return amounts

    mandatory = mandatory_by_category(month_start)
    category_ids = (average_by_category.keys() | current_by_category.keys() | mandatory.keys()) - credit_categories
    projected_expenses = sum((
        max(current_by_category.get(pk, Decimal('0')) / today.day * month_end.day,
            average_by_category.get(pk, Decimal('0')), mandatory.get(pk, Decimal('0')))
        for pk in category_ids
    ), Decimal('0'))
    current_ordinary_expenses = sum(current_by_category.values(), Decimal('0'))
    paid_credit = current.filter(kind=Category.EXPENSE, category_id__in=credit_categories).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    planned_credit = max(debt_payment, sum((mandatory.get(pk, Decimal('0')) for pk in credit_categories), Decimal('0')))
    base_income = max(income, profile.expected_income, average_income)
    debt_ratio = round(float(debt_payment / base_income * 100), 1) if base_income else None
    current_balance = all_income - all_expenses
    remaining_income = max(base_income - income, Decimal('0'))
    remaining_expenses = max(projected_expenses - current_ordinary_expenses, Decimal('0'))
    remaining_credit = max(planned_credit - paid_credit, Decimal('0'))
    expected_balance = current_balance + remaining_income - remaining_expenses - remaining_credit
    overdue = LoanPayment.objects.filter(loan__in=loans, status=LoanPayment.OVERDUE, due_date__lte=today).exists()
    if overdue:
        risk = ('high', 'Есть подтверждённая просрочка', 'Проверьте просроченный платёж и актуальные условия в банке.')
    elif (debt_ratio is not None and debt_ratio > 50) or expected_balance < 0 or (debt_payment and not base_income):
        risk = ('high', 'Высокий риск', 'Проверьте необязательные расходы и ближайшие платежи.')
    elif not transactions.exists():
        risk = ('unknown', 'Недостаточно данных', 'Пока нет подтверждённой истории доходов и расходов.')
    elif (debt_ratio is not None and debt_ratio >= 40) or expenses > base_income * Decimal('0.8'):
        risk = ('medium', 'Требуется внимание', 'Часть бюджета уже израсходована. Сравните траты по категориям.')
    else:
        risk = ('low', 'Ситуация стабильна', 'Продолжайте придерживаться месячного плана.')
    categories = list(current.filter(kind=Category.EXPENSE).values('category__name').annotate(total=Sum('amount')).order_by('-total'))
    available_horizons = [3]
    if data_months >= 6:
        available_horizons.append(6)
    if data_months >= 12:
        available_horizons.append(12)
    forecast_rows = []
    forecast_balance = current_balance
    if data_months:
        for offset in range(1, max(available_horizons) + 1):
            next_mandatory = mandatory_by_category(month_after(month_start, offset))
            ordinary_ids = (average_by_category.keys() | next_mandatory.keys()) - credit_categories
            next_expenses = sum((max(average_by_category.get(pk, Decimal('0')), next_mandatory.get(pk, Decimal('0')))
                                 for pk in ordinary_ids), Decimal('0'))
            next_credit = max(
                sum((loan.monthly_payment for loan in loans if offset <= loan.months_left), Decimal('0')),
                sum((next_mandatory.get(pk, Decimal('0')) for pk in credit_categories), Decimal('0')),
            )
            forecast_balance += (average_income if complete_months else base_income) - next_expenses - next_credit
            if offset in available_horizons:
                forecast_rows.append({'months': offset, 'balance': forecast_balance})

    birth_date = profile.birth_date
    age = None
    reserve_months = 3
    if birth_date:
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        reserve_months = 3 if age < 25 else 6 if age < 45 else 12
    average_expenses = sum(average_by_category.values(), Decimal('0'))
    recommended_reserve = (average_expenses + debt_payment) * reserve_months
    return {
        'income': income, 'expenses': expenses, 'balance': current_balance,
        'debt_payment': debt_payment, 'debt_ratio': debt_ratio,
        'expected_balance': expected_balance, 'risk': risk, 'categories': categories,
        'data_months': data_months, 'forecast_rows': forecast_rows, 'age': age,
        'reserve_months': reserve_months, 'recommended_reserve': recommended_reserve,
        'forecast_provisional': complete_months == 0,
    }
