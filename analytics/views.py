from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone

from accounts.decorators import onboarding_required
from finances.models import SavingsGoal, Transaction
from loans.models import Loan
from .services import build_summary


@login_required
@onboarding_required
def dashboard(request):
    summary = build_summary(request.user)
    context = {
        **summary,
        'transactions': Transaction.objects.filter(user=request.user, operation_date__lte=timezone.localdate()).select_related('category')[:7],
        'goals': SavingsGoal.objects.filter(user=request.user, status=SavingsGoal.ACTIVE)[:4],
        'loans': Loan.objects.filter(user=request.user, is_active=True)[:4],
        'chart_data': {
            'labels': [item['category__name'] for item in summary['categories']],
            'values': [item['total'] for item in summary['categories']],
        },
    }
    return render(request, 'analytics/dashboard.html', context)
