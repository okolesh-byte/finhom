from django.db import migrations


def add_categories(apps, schema_editor):
    Category = apps.get_model('finances', 'Category')
    income = ['Зарплата', 'Подработка', 'Подарки', 'Другие доходы']
    expenses = ['Продукты', 'Транспорт', 'Жильё', 'Связь', 'Здоровье', 'Образование', 'Развлечения', 'Кредиты', 'Другое']
    for name in income:
        Category.objects.get_or_create(name=name, kind='income', owner=None, defaults={'is_system': True})
    for name in expenses:
        Category.objects.get_or_create(name=name, kind='expense', owner=None, defaults={'is_system': True})


def remove_categories(apps, schema_editor):
    Category = apps.get_model('finances', 'Category')
    Category.objects.filter(is_system=True, owner=None).delete()


class Migration(migrations.Migration):
    dependencies = [('finances', '0001_initial')]
    operations = [migrations.RunPython(add_categories, remove_categories)]
