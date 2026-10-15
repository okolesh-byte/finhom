from django.urls import path

from . import views

app_name = 'loans'

urlpatterns = [
    path('', views.loan_list, name='list'),
    path('<int:pk>/', views.loan_detail, name='detail'),
    path('<int:pk>/edit/', views.loan_edit, name='edit'),
    path('<int:pk>/delete/', views.loan_delete, name='delete'),
    path('<int:pk>/payment/', views.add_payment, name='add_payment'),
    path('payments/<int:pk>/edit/', views.payment_edit, name='payment_edit'),
    path('payments/<int:pk>/delete/', views.payment_delete, name='payment_delete'),
    path('<int:pk>/early-repayment/', views.early_repayment, name='early_repayment'),
]
