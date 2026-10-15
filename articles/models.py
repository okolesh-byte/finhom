from django.conf import settings
from django.db import models


class ArticleCategory(models.Model):
    name = models.CharField('Название', max_length=80, unique=True)
    slug = models.SlugField('Адрес', unique=True)

    def __str__(self):
        return self.name


class Article(models.Model):
    category = models.ForeignKey(ArticleCategory, on_delete=models.PROTECT, related_name='articles')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='articles')
    title = models.CharField('Заголовок', max_length=180)
    summary = models.CharField('Краткое описание', max_length=300)
    body = models.TextField('Текст')
    cover = models.ImageField('Обложка', upload_to='articles/', blank=True)
    published_at = models.DateTimeField('Дата публикации', null=True, blank=True)
    is_published = models.BooleanField('Опубликовано', default=False)

    class Meta:
        ordering = ['-published_at', '-id']

    def __str__(self):
        return self.title


class Comment(models.Model):
    PENDING = 'pending'
    PUBLISHED = 'published'
    REJECTED = 'rejected'
    STATUSES = [(PENDING, 'На проверке'), (PUBLISHED, 'Опубликован'), (REJECTED, 'Отклонён')]

    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='comments')
    text = models.TextField('Комментарий', max_length=1000)
    status = models.CharField('Статус', max_length=12, choices=STATUSES, default=PENDING)
    moderator_note = models.CharField('Причина решения', max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']


class TopicSuggestion(models.Model):
    PENDING = 'pending'
    ACCEPTED = 'accepted'
    REJECTED = 'rejected'
    STATUSES = [(PENDING, 'На рассмотрении'), (ACCEPTED, 'Принято'), (REJECTED, 'Отклонено')]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='topic_suggestions')
    title = models.CharField('Название темы', max_length=180)
    description = models.TextField('Описание', max_length=1500)
    status = models.CharField('Статус', max_length=12, choices=STATUSES, default=PENDING)
    moderator_note = models.CharField('Ответ администратора', max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
