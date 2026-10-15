from django.conf import settings
from django.db import models


class Forecast(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='forecasts')
    period_months = models.PositiveSmallIntegerField('Период анализа')
    expected_income = models.DecimalField('Ожидаемые доходы', max_digits=12, decimal_places=2)
    expected_expenses = models.DecimalField('Ожидаемые расходы', max_digits=12, decimal_places=2)
    expected_balance = models.DecimalField('Ожидаемый баланс', max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)


class RiskAlert(models.Model):
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    LEVELS = [(LOW, 'Низкий'), (MEDIUM, 'Средний'), (HIGH, 'Высокий')]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='risk_alerts')
    level = models.CharField('Уровень', max_length=10, choices=LEVELS)
    title = models.CharField('Название', max_length=150)
    reason = models.TextField('Причина')
    recommendation = models.TextField('Рекомендация')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField('Активно', default=True)
