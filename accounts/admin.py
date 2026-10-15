from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Profile, User


@admin.register(User)
class FinhomUserAdmin(UserAdmin):
    ordering = ('email',)
    list_display = ('email', 'first_name', 'is_staff', 'is_active')
    search_fields = ('email', 'first_name')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Личные данные', {'fields': ('first_name',)}),
        ('Права', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Даты', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = ((None, {'classes': ('wide',), 'fields': ('email', 'first_name', 'password1', 'password2')}),)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'birth_date', 'expected_income', 'onboarding_completed')
    list_filter = ('onboarding_completed',)
