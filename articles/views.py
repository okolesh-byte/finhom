from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.db.models import Case, Count, IntegerField, Q, Value, When
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import CommentForm, ModeratorCommentForm, ModeratorSuggestionForm, TopicSuggestionForm
from .models import Article, Comment, TopicSuggestion


@login_required
def article_list(request):
    articles = Article.objects.filter(is_published=True).select_related('category', 'author')
    return render(request, 'articles/list.html', {'articles': articles})


@login_required
def article_detail(request, pk):
    article = get_object_or_404(Article.objects.select_related('category', 'author'), pk=pk, is_published=True)
    form = CommentForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        comment = form.save(commit=False)
        comment.article = article
        comment.author = request.user
        comment.save()
        messages.success(request, 'Комментарий отправлен на модерацию.')
        return redirect('articles:detail', pk=article.pk)
    comments = article.comments.filter(status=Comment.PUBLISHED).select_related('author')
    own_comments = article.comments.filter(author=request.user).exclude(status=Comment.PUBLISHED)
    return render(request, 'articles/detail.html', {
        'article': article, 'comments': comments, 'own_comments': own_comments, 'form': form,
    })


@login_required
def suggest_topic(request):
    form = TopicSuggestionForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        item = form.save(commit=False)
        item.user = request.user
        item.save()
        messages.success(request, 'Тема отправлена на рассмотрение.')
        return redirect('articles:suggest')
    suggestions = TopicSuggestion.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'articles/suggest.html', {'form': form, 'suggestions': suggestions})


@staff_member_required
def moderation_dashboard(request):
    permissions = ('articles.change_comment', 'articles.change_topicsuggestion', 'articles.change_article')
    if not any(request.user.has_perm(permission) for permission in permissions):
        raise PermissionDenied
    comments = Comment.objects.select_related('article', 'author').annotate(
        review_order=Case(When(status=Comment.PENDING, then=Value(0)), default=Value(1), output_field=IntegerField()),
    ).order_by('review_order', '-created_at')
    suggestions = TopicSuggestion.objects.select_related('user').annotate(
        review_order=Case(When(status=TopicSuggestion.PENDING, then=Value(0)), default=Value(1), output_field=IntegerField()),
    ).order_by('review_order', '-created_at')
    articles = Article.objects.select_related('category', 'author').annotate(
        comments_count=Count('comments'),
        pending_comments_count=Count('comments', filter=Q(comments__status=Comment.PENDING)),
    )
    if not request.user.has_perm('articles.change_comment'):
        comments = comments.none()
    if not request.user.has_perm('articles.change_topicsuggestion'):
        suggestions = suggestions.none()
    if not request.user.has_perm('articles.change_article'):
        articles = articles.none()
    context = {
        'comments': comments,
        'suggestions': suggestions,
        'articles': articles,
        'pending_comments': comments.filter(status=Comment.PENDING).count(),
        'pending_suggestions': suggestions.filter(status=TopicSuggestion.PENDING).count(),
    }
    return render(request, 'articles/moderation.html', context)


@staff_member_required
@permission_required('articles.change_comment', raise_exception=True)
@require_POST
def moderate_comment(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    form = ModeratorCommentForm(request.POST, instance=comment)
    if form.is_valid():
        form.save()
        messages.success(request, 'Комментарий обновлён.')
    else:
        messages.error(request, 'Не удалось обновить комментарий. Проверьте поля.')
    return redirect('articles:moderation')


@staff_member_required
@permission_required('articles.change_topicsuggestion', raise_exception=True)
@require_POST
def moderate_suggestion(request, pk):
    suggestion = get_object_or_404(TopicSuggestion, pk=pk)
    form = ModeratorSuggestionForm(request.POST, instance=suggestion)
    if form.is_valid():
        form.save()
        messages.success(request, 'Решение по теме сохранено.')
    else:
        messages.error(request, 'Не удалось сохранить решение по теме.')
    return redirect('articles:moderation')


@staff_member_required
@permission_required('articles.change_article', raise_exception=True)
@require_POST
def toggle_article(request, pk):
    article = get_object_or_404(Article, pk=pk)
    article.is_published = not article.is_published
    if article.is_published and not article.published_at:
        article.published_at = timezone.now()
    article.save(update_fields=['is_published', 'published_at'])
    state = 'опубликована' if article.is_published else 'снята с публикации'
    messages.success(request, f'Статья «{article.title}» {state}.')
    return redirect('articles:moderation')
