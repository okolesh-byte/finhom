from django import forms
from django.db.models import Q
from django.utils import timezone

from .models import Category, MonthlyBudget, RecurringPayment, SavingsContribution, SavingsGoal, Transaction


class UserCategoryMixin:
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if 'category' in self.fields and user:
            self.fields['category'].queryset = Category.objects.filter(Q(is_system=True) | Q(owner=user))
            self.fields['category'].label = 'Категория'
            self.fields['category'].empty_label = 'Выберите категорию'


class TransactionForm(UserCategoryMixin, forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ('kind', 'category', 'amount', 'operation_date', 'note')
        widgets = {'operation_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'})}

    def clean_operation_date(self):
        value = self.cleaned_data['operation_date']
        if value > timezone.localdate():
            raise forms.ValidationError('Укажите дату совершённой операции, не позже сегодняшнего дня.')
        return value

    def clean(self):
        data = super().clean()
        category = data.get('category')
        if category and category.kind != data.get('kind'):
            self.add_error('category', 'Категория не соответствует типу операции.')
        return data


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ('name', 'kind')


class BudgetForm(UserCategoryMixin, forms.ModelForm):
    month = forms.DateField(label='Месяц', input_formats=['%Y-%m'], widget=forms.DateInput(format='%Y-%m', attrs={'type': 'month'}))

    class Meta:
        model = MonthlyBudget
        fields = ('category', 'month', 'limit')

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, user=user, **kwargs)
        self.fields['category'].queryset = self.fields['category'].queryset.filter(kind=Category.EXPENSE)

    def clean_month(self):
        value = self.cleaned_data['month']
        return value.replace(day=1)


class RecurringPaymentForm(UserCategoryMixin, forms.ModelForm):
    class Meta:
        model = RecurringPayment
        fields = ('name', 'category', 'amount', 'day', 'start_date')
        widgets = {
            'day': forms.NumberInput(attrs={'min': 1, 'max': 31}),
            'start_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, user=user, **kwargs)
        self.fields['category'].queryset = self.fields['category'].queryset.filter(kind=Category.EXPENSE)

    def clean_day(self):
        value = self.cleaned_data['day']
        if not 1 <= value <= 31:
            raise forms.ValidationError('Укажите день от 1 до 31.')
        return value


class SavingsGoalForm(forms.ModelForm):
    class Meta:
        model = SavingsGoal
        fields = ('name', 'target_amount', 'current_amount', 'target_date', 'description')
        widgets = {'target_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'})}

    def clean_current_amount(self):
        value = self.cleaned_data['current_amount']
        if value < 0:
            raise forms.ValidationError('Накопленная сумма не может быть отрицательной.')
        return value


class SavingsContributionForm(forms.ModelForm):
    class Meta:
        model = SavingsContribution
        fields = ('amount', 'contribution_date', 'note')
        widgets = {'contribution_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'})}

    def clean_contribution_date(self):
        value = self.cleaned_data['contribution_date']
        if value > timezone.localdate():
            raise forms.ValidationError('Дата пополнения не может быть в будущем.')
        return value
