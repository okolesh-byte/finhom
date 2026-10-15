from django.db import migrations


def add_categories(apps, schema_editor):
    Category = apps.get_model('articles', 'ArticleCategory')
    items = [
        ('Бюджет', 'budget'), ('Долги', 'debts'), ('Накопления', 'savings'),
        ('Кредиты', 'loans'), ('Финансовая безопасность', 'security'),
        ('Полезные привычки', 'habits'),
    ]
    for name, slug in items:
        Category.objects.get_or_create(slug=slug, defaults={'name': name})


def remove_categories(apps, schema_editor):
    apps.get_model('articles', 'ArticleCategory').objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [('articles', '0001_initial')]
    operations = [migrations.RunPython(add_categories, remove_categories)]
