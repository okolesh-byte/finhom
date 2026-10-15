from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Loan(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='loans')
    name = models.CharField('Название кредита', max_length=120)
    bank = models.CharField('Банк', max_length=120)
    original_amount = models.DecimalField('Первоначальная сумма', max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)])
    current_balance = models.DecimalField('Текущий остаток', max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    annual_rate = models.DecimalField('Годовая ставка, %', max_digits=6, decimal_places=2, validators=[MinValueValidator(0)])
    monthly_payment = models.DecimalField('Платёж по данным банка', max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)])
    start_date = models.DateField('Дата оформления')
    end_date = models.DateField('Дата окончания')
    payment_day = models.PositiveSmallIntegerField('День платежа')
    months_left = models.PositiveIntegerField('Осталось месяцев')
    is_active = models.BooleanField('Активен', default=True)

    def __str__(self):
        return self.name


class LoanPayment(models.Model):
    PLANNED = 'planned'
    EARLY = 'early'
    ON_TIME = 'on_time'
    LATE = 'late'
    PARTIAL = 'partial'
    UNCONFIRMED = 'unconfirmed'
    OVERDUE = 'overdue'
    STATUSES = [
        (PLANNED, 'Запланирован'), (EARLY, 'Оплачен заранее'),
        (ON_TIME, 'Оплачен вовремя'), (LATE, 'Оплачен с опозданием'), (PARTIAL, 'Оплачен частично'),
        (UNCONFIRMED, 'Статус не подтверждён'), (OVERDUE, 'Просрочен'),
    ]

    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='payments')
    due_date = models.DateField('Плановая дата')
    planned_amount = models.DecimalField('Плановая сумма', max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)])
    actual_date = models.DateField('Фактическая дата', null=True, blank=True)
    actual_amount = models.DecimalField('Фактическая сумма', max_digits=12, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0.01)])
    status = models.CharField('Статус', max_length=15, choices=STATUSES, default=PLANNED)
    note = models.CharField('Заметка', max_length=250, blank=True)

    class Meta:
        ordering = ['due_date']
        constraints = [models.UniqueConstraint(fields=['loan', 'due_date'], name='unique_loan_due_date')]


class EarlyRepayment(models.Model):
    REDUCE_PAYMENT = 'payment'
    REDUCE_TERM = 'term'
    STRATEGIES = [(REDUCE_PAYMENT, 'Уменьшить платёж'), (REDUCE_TERM, 'Уменьшить срок')]

    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='early_repayments')
    amount = models.DecimalField('Сумма', max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)])
    repayment_date = models.DateField('Дата')
    strategy = models.CharField('Вариант', max_length=10, choices=STRATEGIES)
    old_balance = models.DecimalField('Предыдущий остаток', max_digits=12, decimal_places=2)
    new_balance = models.DecimalField('Новый остаток', max_digits=12, decimal_places=2)
    estimated_payment = models.DecimalField('Примерный новый платёж', max_digits=12, decimal_places=2, null=True, blank=True)
    estimated_months = models.PositiveIntegerField('Примерный новый срок', null=True, blank=True)
