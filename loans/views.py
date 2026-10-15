from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.decorators import onboarding_required
from .forms import EarlyRepaymentForm, LoanForm, LoanPaymentForm
from .models import Loan, LoanPayment
from .services import calculate_early_repayment


@login_required
@onboarding_required
def loan_list(request):
    form = LoanForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        loan = form.save(commit=False)
        loan.user = request.user
        loan.save()
        messages.success(request, 'Кредит добавлен.')
        return redirect('loans:list')
    return render(request, 'loans/list.html', {'form': form, 'loans': Loan.objects.filter(user=request.user)})


@login_required
@onboarding_required
def loan_detail(request, pk):
    loan = get_object_or_404(Loan, pk=pk, user=request.user)
    return render(request, 'loans/detail.html', {'loan': loan})


@login_required
@onboarding_required
def loan_edit(request, pk):
    loan = get_object_or_404(Loan, pk=pk, user=request.user)
    form = LoanForm(request.POST or None, instance=loan)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Данные кредита обновлены.')
        return redirect('loans:detail', pk=loan.pk)
    return render(request, 'finances/form.html', {'form': form, 'title': f'Изменить «{loan.name}»'})


@login_required
@onboarding_required
@require_POST
def loan_delete(request, pk):
    loan = get_object_or_404(Loan, pk=pk, user=request.user)
    loan.delete()
    messages.success(request, 'Кредит удалён.')
    return redirect('loans:list')


@login_required
@onboarding_required
def add_payment(request, pk):
    loan = get_object_or_404(Loan, pk=pk, user=request.user)
    form = LoanPaymentForm(request.POST or None, loan=loan, initial={'planned_amount': loan.monthly_payment})
    if request.method == 'POST' and form.is_valid():
        item = form.save(commit=False)
        item.loan = loan
        item.save()
        messages.success(request, 'Платёж сохранён.')
        return redirect('loans:detail', pk=loan.pk)
    return render(request, 'finances/form.html', {'form': form, 'title': 'Добавить платёж'})


@login_required
@onboarding_required
def payment_edit(request, pk):
    payment = get_object_or_404(LoanPayment, pk=pk, loan__user=request.user)
    form = LoanPaymentForm(request.POST or None, instance=payment, loan=payment.loan)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Платёж обновлён.')
        return redirect('loans:detail', pk=payment.loan_id)
    return render(request, 'finances/form.html', {'form': form, 'title': 'Изменить платёж'})


@login_required
@onboarding_required
@require_POST
def payment_delete(request, pk):
    payment = get_object_or_404(LoanPayment, pk=pk, loan__user=request.user)
    loan_id = payment.loan_id
    payment.delete()
    messages.success(request, 'Платёж удалён.')
    return redirect('loans:detail', pk=loan_id)


@login_required
@onboarding_required
def early_repayment(request, pk):
    loan = get_object_or_404(Loan, pk=pk, user=request.user)
    form = EarlyRepaymentForm(request.POST or None, loan=loan, initial={'repayment_date': date.today()})
    if request.method == 'POST' and form.is_valid():
        try:
            result = calculate_early_repayment(loan, form.cleaned_data['amount'], form.cleaned_data['strategy'])
        except ValidationError as error:
            form.add_error(None, error)
        else:
            item = form.save(commit=False)
            item.loan = loan
            item.old_balance = loan.current_balance
            item.new_balance = result['new_balance']
            item.estimated_payment = result['estimated_payment']
            item.estimated_months = result['estimated_months']
            item.save()
            messages.success(request, 'Предварительный расчёт сохранён.')
            return redirect('loans:early_repayment', pk=loan.pk)
    return render(request, 'loans/early_repayment.html', {'form': form, 'loan': loan})
