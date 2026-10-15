from django import forms
from django.utils import timezone

from .models import EarlyRepayment, Loan, LoanPayment


class LoanForm(forms.ModelForm):
    class Meta:
        model = Loan
        fields = ('name', 'bank', 'original_amount', 'current_balance', 'annual_rate', 'monthly_payment', 'start_date', 'end_date', 'payment_day', 'months_left', 'is_active')
        widgets = {
            'start_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            'end_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            'payment_day': forms.NumberInput(attrs={'min': 1, 'max': 31}),
        }

    def clean(self):
        data = super().clean()
        original = data.get('original_amount')
        balance = data.get('current_balance')
        start = data.get('start_date')
        end = data.get('end_date')
        day = data.get('payment_day')
        if original is not None and balance is not None and balance > original:
            self.add_error('current_balance', 'Остаток не может быть больше первоначальной суммы.')
        if start and end and end <= start:
            self.add_error('end_date', 'Дата окончания должна быть позже даты оформления.')
        if day is not None and not 1 <= day <= 31:
            self.add_error('payment_day', 'Укажите день от 1 до 31.')
        if data.get('is_active') and not data.get('months_left'):
            self.add_error('months_left', 'Для действующего кредита укажите оставшийся срок больше нуля.')
        return data


class LoanPaymentForm(forms.ModelForm):
    class Meta:
        model = LoanPayment
        fields = ('due_date', 'planned_amount', 'actual_date', 'actual_amount', 'status', 'note')
        widgets = {
            'due_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            'actual_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
        }

    def __init__(self, *args, loan=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.loan = loan

    def clean(self):
        data = super().clean()
        status = data.get('status')
        actual_date = data.get('actual_date')
        actual_amount = data.get('actual_amount')
        paid_statuses = {LoanPayment.EARLY, LoanPayment.ON_TIME, LoanPayment.LATE, LoanPayment.PARTIAL}
        due_date = data.get('due_date')
        planned = data.get('planned_amount')
        if status in paid_statuses and not actual_date:
            self.add_error('actual_date', 'Для оплаченного платежа укажите фактическую дату.')
        if status in paid_statuses and not actual_amount:
            self.add_error('actual_amount', 'Для оплаченного платежа укажите сумму.')
        if actual_date and actual_date > timezone.localdate():
            self.add_error('actual_date', 'Фактический платёж не может быть в будущем.')
        if actual_amount is not None and not actual_date:
            self.add_error('actual_date', 'Укажите дату внесения суммы.')
        if actual_date and actual_amount is None:
            self.add_error('actual_amount', 'Укажите внесённую сумму.')
        if status in {LoanPayment.PLANNED, LoanPayment.UNCONFIRMED} and (actual_date or actual_amount is not None):
            self.add_error('status', 'Укажите статус оплаченного платежа.')
        if status in {LoanPayment.EARLY, LoanPayment.ON_TIME, LoanPayment.LATE} and planned and actual_amount is not None:
            if actual_amount < planned:
                self.add_error('status', 'Сумма меньше плановой. Выберите частичную оплату.')
            elif actual_date and due_date:
                data['status'] = (LoanPayment.EARLY if actual_date < due_date else
                                  LoanPayment.ON_TIME if actual_date == due_date else LoanPayment.LATE)
        if status == LoanPayment.PARTIAL and planned and actual_amount is not None and actual_amount >= planned:
            self.add_error('status', 'Платёж внесён полностью. Выберите статус полной оплаты.')
        if self.loan and due_date:
            duplicates = LoanPayment.objects.filter(loan=self.loan, due_date=due_date).exclude(pk=self.instance.pk)
            if duplicates.exists():
                self.add_error('due_date', 'Платёж на эту дату уже есть. Измените существующую запись.')
        return data


class EarlyRepaymentForm(forms.ModelForm):
    class Meta:
        model = EarlyRepayment
        fields = ('amount', 'repayment_date', 'strategy')
        widgets = {'repayment_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'})}

    def __init__(self, *args, loan=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.loan = loan

    def clean_amount(self):
        value = self.cleaned_data['amount']
        if self.loan and value > self.loan.current_balance:
            raise forms.ValidationError('Сумма не может быть больше текущего остатка кредита.')
        return value
