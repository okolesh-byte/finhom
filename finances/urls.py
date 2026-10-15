from django.urls import path

from . import views

app_name = 'finances'

urlpatterns = [
    path('transactions/', views.transaction_list, name='transactions'),
    path('transactions/export/', views.transaction_export, name='transaction_export'),
    path('transactions/add/', views.transaction_create, name='transaction_create'),
    path('transactions/<int:pk>/edit/', views.transaction_edit, name='transaction_edit'),
    path('transactions/<int:pk>/delete/', views.transaction_delete, name='transaction_delete'),
    path('planning/', views.planning, name='planning'),
    path('planning/budgets/<int:pk>/delete/', views.budget_delete, name='budget_delete'),
    path('planning/recurring/<int:pk>/edit/', views.recurring_edit, name='recurring_edit'),
    path('planning/recurring/<int:pk>/delete/', views.recurring_delete, name='recurring_delete'),
    path('goals/', views.goals, name='goals'),
    path('goals/<int:pk>/contribute/', views.goal_contribute, name='goal_contribute'),
    path('goals/<int:pk>/edit/', views.goal_edit, name='goal_edit'),
    path('goals/<int:pk>/delete/', views.goal_delete, name='goal_delete'),
]
