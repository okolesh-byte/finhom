from django.contrib import admin
from django.utils import timezone

from .models import Article, ArticleCategory, Comment, TopicSuggestion


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'author', 'is_published', 'published_at')
    list_filter = ('is_published', 'category')
    search_fields = ('title', 'summary', 'body')
    actions = ('publish_articles', 'unpublish_articles')

    @admin.action(description='Опубликовать выбранные статьи')
    def publish_articles(self, request, queryset):
        queryset.update(is_published=True, published_at=timezone.now())

    @admin.action(description='Снять выбранные статьи с публикации')
    def unpublish_articles(self, request, queryset):
        queryset.update(is_published=False)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('short_text', 'article', 'author', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('text', 'author__email')
    actions = ('publish_comments', 'reject_comments')
    readonly_fields = ('created_at', 'updated_at')

    @admin.display(description='Комментарий')
    def short_text(self, obj):
        return obj.text[:70]

    @admin.action(description='Опубликовать выбранные комментарии')
    def publish_comments(self, request, queryset):
        queryset.update(status=Comment.PUBLISHED, moderator_note='')

    @admin.action(description='Отклонить выбранные комментарии')
    def reject_comments(self, request, queryset):
        queryset.update(status=Comment.REJECTED)


@admin.register(TopicSuggestion)
class TopicSuggestionAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('title', 'description')
    actions = ('accept_suggestions', 'reject_suggestions')

    @admin.action(description='Принять выбранные темы')
    def accept_suggestions(self, request, queryset):
        queryset.update(status=TopicSuggestion.ACCEPTED)

    @admin.action(description='Отклонить выбранные темы')
    def reject_suggestions(self, request, queryset):
        queryset.update(status=TopicSuggestion.REJECTED)


admin.site.register(ArticleCategory)
