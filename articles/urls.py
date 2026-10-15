from django.urls import path

from . import views

app_name = 'articles'

urlpatterns = [
    path('', views.article_list, name='list'),
    path('suggest/', views.suggest_topic, name='suggest'),
    path('moderation/', views.moderation_dashboard, name='moderation'),
    path('moderation/comments/<int:pk>/', views.moderate_comment, name='moderate_comment'),
    path('moderation/suggestions/<int:pk>/', views.moderate_suggestion, name='moderate_suggestion'),
    path('moderation/articles/<int:pk>/toggle/', views.toggle_article, name='toggle_article'),
    path('<int:pk>/', views.article_detail, name='detail'),
]
