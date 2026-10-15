from django.contrib import admin

from .models import Category, MonthlyBudget, RecurringPayment, SavingsContribution, SavingsGoal, Transaction


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'kind', 'is_system', 'owner')
    list_filter = ('kind', 'is_system')
    search_fields = ('name',)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'operation_date', 'kind', 'category', 'amount')
    list_filter = ('kind', 'category', 'operation_date')


admin.site.register(MonthlyBudget)
admin.site.register(RecurringPayment)
admin.site.register(SavingsGoal)
admin.site.register(SavingsContribution)
