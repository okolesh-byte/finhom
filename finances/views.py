import csv
from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.db import transaction as db_transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.decorators import onboarding_required
from .forms import BudgetForm, CategoryForm, RecurringPaymentForm, SavingsContributionForm, SavingsGoalForm, TransactionForm
from .models import Category, MonthlyBudget, RecurringPayment, SavingsGoal, Transaction


@login_required
@onboarding_required
def transaction_list(request):
    transactions = Transaction.objects.filter(user=request.user).select_related('category')
    return render(request, 'finances/transactions.html', {'transactions': transactions})


@login_required
@onboarding_required
def transaction_export(request):
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="finhom-transactions.csv"'
    response.write('\ufeff')
    writer = csv.writer(response, delimiter=';')
    writer.writerow(['Дата', 'Тип', 'Категория', 'Сумма', 'Заметка'])
    transactions = Transaction.objects.filter(user=request.user).select_related('category')
    def safe_cell(value):
        if value.lstrip().startswith(('=', '+', '-', '@')) or value.startswith(('\t', '\r', '\n')):
            return "'" + value
        return value

    for item in transactions:
        writer.writerow([item.operation_date.strftime('%d.%m.%Y'), item.get_kind_display(), safe_cell(item.category.name), item.amount, safe_cell(item.note)])
    return response


@login_required
@onboarding_required
def transaction_create(request):
    form = TransactionForm(request.POST or None, user=request.user, initial={'operation_date': date.today()})
    if request.method == 'POST' and form.is_valid():
        transaction = form.save(commit=False)
        transaction.user = request.user
        transaction.save()
        messages.success(request, 'Операция добавлена.')
        return redirect('finances:transactions')
    return render(request, 'finances/form.html', {'form': form, 'title': 'Новая операция'})


@login_required
@onboarding_required
def transaction_edit(request, pk):
    item = get_object_or_404(Transaction, pk=pk, user=request.user)
    form = TransactionForm(request.POST or None, instance=item, user=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Операция обновлена.')
        return redirect('finances:transactions')
    return render(request, 'finances/form.html', {'form': form, 'title': 'Изменить операцию'})


@login_required
@onboarding_required
def transaction_delete(request, pk):
    item = get_object_or_404(Transaction, pk=pk, user=request.user)
    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Операция удалена.')
    return redirect('finances:transactions')


@login_required
@onboarding_required
def planning(request):
    action = request.POST.get('action') if request.method == 'POST' else None
    budget_form = BudgetForm(request.POST if action == 'budget' else None, user=request.user, prefix='budget')
    category_form = CategoryForm(request.POST if action == 'category' else None, prefix='category')
    recurring_form = RecurringPaymentForm(request.POST if action == 'recurring' else None, user=request.user, prefix='recurring', initial={'start_date': date.today()})
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'budget' and budget_form.is_valid():
            item = budget_form.save(commit=False)
            MonthlyBudget.objects.update_or_create(
                user=request.user,
                category=item.category,
                month=item.month,
                defaults={'limit': item.limit},
            )
            messages.success(request, 'Бюджет сохранён.')
            return redirect('finances:planning')
        if action == 'category' and category_form.is_valid():
            name = category_form.cleaned_data['name'].strip()
            kind = category_form.cleaned_data['kind']
            if Category.objects.filter(owner=request.user, name__iexact=name, kind=kind).exists():
                category_form.add_error('name', 'Такая категория уже существует.')
            else:
                item = category_form.save(commit=False)
                item.name = name
                item.owner = request.user
                item.save()
                messages.success(request, 'Категория добавлена.')
                return redirect('finances:planning')
        if action == 'recurring' and recurring_form.is_valid():
            item = recurring_form.save(commit=False)
            item.user = request.user
            item.save()
            messages.success(request, 'Обязательный платёж добавлен.')
            return redirect('finances:planning')
    budgets = MonthlyBudget.objects.filter(user=request.user).select_related('category').order_by('-month')
    current = date.today().replace(day=1)
    for budget in budgets:
        spent = Transaction.objects.filter(user=request.user, category=budget.category, kind=Category.EXPENSE, operation_date__lte=date.today(), operation_date__year=budget.month.year, operation_date__month=budget.month.month).aggregate(total=Sum('amount'))['total'] or 0
        budget.spent = spent
        budget.percent = min(round(float(spent / budget.limit * 100)), 999) if budget.limit else 0
    context = {
        'budget_form': budget_form, 'category_form': category_form, 'recurring_form': recurring_form,
        'budgets': budgets, 'recurring': RecurringPayment.objects.filter(user=request.user),
        'custom_categories': Category.objects.filter(owner=request.user), 'current_month': current,
    }
    return render(request, 'finances/planning.html', context)


@login_required
@onboarding_required
@require_POST
def budget_delete(request, pk):
    budget = get_object_or_404(MonthlyBudget, pk=pk, user=request.user)
    budget.delete()
    messages.success(request, 'Бюджет удалён.')
    return redirect('finances:planning')


@login_required
@onboarding_required
def recurring_edit(request, pk):
    item = get_object_or_404(RecurringPayment, pk=pk, user=request.user)
    form = RecurringPaymentForm(request.POST or None, instance=item, user=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Обязательный платёж обновлён.')
        return redirect('finances:planning')
    return render(request, 'finances/form.html', {'form': form, 'title': 'Изменить обязательный платёж'})


@login_required
@onboarding_required
@require_POST
def recurring_delete(request, pk):
    item = get_object_or_404(RecurringPayment, pk=pk, user=request.user)
    item.delete()
    messages.success(request, 'Обязательный платёж удалён.')
    return redirect('finances:planning')


@login_required
@onboarding_required
def goals(request):
    form = SavingsGoalForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        item = form.save(commit=False)
        item.user = request.user
        item.status = SavingsGoal.COMPLETED if item.current_amount >= item.target_amount else SavingsGoal.ACTIVE
        item.save()
        messages.success(request, 'Накопительный конверт создан.')
        return redirect('finances:goals')
    return render(request, 'finances/goals.html', {'form': form, 'goals': SavingsGoal.objects.filter(user=request.user)})


@login_required
@onboarding_required
def goal_contribute(request, pk):
    goal = get_object_or_404(SavingsGoal, pk=pk, user=request.user)
    form = SavingsContributionForm(request.POST or None, initial={'contribution_date': date.today()})
    if request.method == 'POST' and form.is_valid():
        with db_transaction.atomic():
            goal.refresh_from_db()
            contribution = form.save(commit=False)
            contribution.goal = goal
            contribution.save()
            goal.current_amount += contribution.amount
            if goal.current_amount >= goal.target_amount:
                goal.status = SavingsGoal.COMPLETED
            goal.save(update_fields=['current_amount', 'status'])
        messages.success(request, 'Пополнение добавлено.')
        return redirect('finances:goals')
    return render(request, 'finances/form.html', {'form': form, 'title': f'Пополнить «{goal.name}»'})


@login_required
@onboarding_required
def goal_edit(request, pk):
    goal = get_object_or_404(SavingsGoal, pk=pk, user=request.user)
    form = SavingsGoalForm(request.POST or None, instance=goal)
    if request.method == 'POST' and form.is_valid():
        goal = form.save(commit=False)
        goal.status = SavingsGoal.COMPLETED if goal.current_amount >= goal.target_amount else SavingsGoal.ACTIVE
        goal.save()
        messages.success(request, 'Цель обновлена.')
        return redirect('finances:goals')
    return render(request, 'finances/form.html', {'form': form, 'title': f'Изменить «{goal.name}»'})


@login_required
@onboarding_required
@require_POST
def goal_delete(request, pk):
    goal = get_object_or_404(SavingsGoal, pk=pk, user=request.user)
    goal.delete()
    messages.success(request, 'Накопительная цель удалена.')
    return redirect('finances:goals')
