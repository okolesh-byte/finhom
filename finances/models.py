from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Category(models.Model):
    INCOME = 'income'
    EXPENSE = 'expense'
    TYPES = [(INCOME, 'Доход'), (EXPENSE, 'Расход')]

    name = models.CharField('Название', max_length=80)
    kind = models.CharField('Тип', max_length=10, choices=TYPES)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='categories')
    is_system = models.BooleanField('Системная', default=False)

    class Meta:
        ordering = ['kind', 'name']
        constraints = [models.UniqueConstraint(fields=['name', 'kind', 'owner'], name='unique_user_category')]

    def __str__(self):
        return self.name


class Transaction(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transactions')
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='transactions')
    kind = models.CharField('Тип', max_length=10, choices=Category.TYPES)
    amount = models.DecimalField('Сумма', max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)])
    operation_date = models.DateField('Дата операции')
    note = models.CharField('Заметка', max_length=250, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-operation_date', '-id']

    def __str__(self):
        return f'{self.get_kind_display()}: {self.amount}'


class MonthlyBudget(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='budgets')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='budgets', limit_choices_to={'kind': Category.EXPENSE})
    month = models.DateField('Месяц')
    limit = models.DecimalField('Лимит', max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)])

    class Meta:
        constraints = [models.UniqueConstraint(fields=['user', 'category', 'month'], name='unique_monthly_budget')]


class RecurringPayment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='recurring_payments')
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='recurring_payments')
    name = models.CharField('Название', max_length=120)
    amount = models.DecimalField('Сумма', max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)])
    day = models.PositiveSmallIntegerField('День месяца')
    start_date = models.DateField('Дата начала')
    is_active = models.BooleanField('Активен', default=True)


class SavingsGoal(models.Model):
    ACTIVE = 'active'
    COMPLETED = 'completed'
    STATUSES = [(ACTIVE, 'Активна'), (COMPLETED, 'Достигнута')]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='savings_goals')
    name = models.CharField('Название конверта', max_length=120)
    target_amount = models.DecimalField('Целевая сумма', max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)])
    current_amount = models.DecimalField('Накоплено', max_digits=12, decimal_places=2, default=0)
    target_date = models.DateField('Желаемая дата', null=True, blank=True)
    description = models.CharField('Описание', max_length=250, blank=True)
    status = models.CharField('Статус', max_length=12, choices=STATUSES, default=ACTIVE)

    @property
    def progress(self):
        if not self.target_amount:
            return 0
        return min(round(float(self.current_amount / self.target_amount * 100)), 100)


class SavingsContribution(models.Model):
    goal = models.ForeignKey(SavingsGoal, on_delete=models.CASCADE, related_name='contributions')
    amount = models.DecimalField('Сумма', max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)])
    contribution_date = models.DateField('Дата')
    note = models.CharField('Заметка', max_length=250, blank=True)
