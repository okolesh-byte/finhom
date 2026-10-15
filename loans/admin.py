from django.contrib import admin

from .models import EarlyRepayment, Loan, LoanPayment


class LoanPaymentInline(admin.TabularInline):
    model = LoanPayment
    extra = 0


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'bank', 'current_balance', 'monthly_payment', 'is_active')
    list_filter = ('is_active', 'bank')
    inlines = (LoanPaymentInline,)


admin.site.register(EarlyRepayment)
