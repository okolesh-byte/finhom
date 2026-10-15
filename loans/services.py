import math
from decimal import Decimal, ROUND_HALF_UP

from django.core.exceptions import ValidationError

from .models import EarlyRepayment


def calculate_early_repayment(loan, amount, strategy):
    if not loan.is_active or loan.current_balance <= 0:
        raise ValidationError('Расчёт доступен только для действующего кредита с остатком.')
    if amount <= 0 or amount > loan.current_balance:
        raise ValidationError('Укажите сумму больше нуля и не больше остатка кредита.')
    if loan.months_left < 1 or loan.monthly_payment <= 0:
        raise ValidationError('Проверьте оставшийся срок и платёж по данным банка.')

    balance = loan.current_balance - amount
    if balance == 0:
        return {'new_balance': balance, 'estimated_payment': Decimal('0'), 'estimated_months': 0}

    rate = loan.annual_rate / Decimal('1200')
    if strategy == EarlyRepayment.REDUCE_PAYMENT:
        payment = (balance * rate / (1 - (1 + rate) ** -loan.months_left)
                   if rate else balance / loan.months_left)
        months = loan.months_left
    else:
        payment = loan.monthly_payment
        if rate and payment <= balance * rate:
            raise ValidationError('Платёж не покрывает месячные проценты. Проверьте данные банка или выберите уменьшение платежа.')
        months = (math.ceil(-math.log1p(-float(balance * rate / payment)) / math.log1p(float(rate)))
                  if rate else math.ceil(balance / payment))

    return {
        'new_balance': balance,
        'estimated_payment': payment.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
        'estimated_months': months,
    }
