from datetime import date

from django.test import TestCase
from django.core import mail
from django.test import override_settings
from django.urls import reverse
from django.contrib.auth import authenticate

from .models import Profile, User


class RegistrationTests(TestCase):
    def test_registration_creates_profile_and_logs_user_in(self):
        response = self.client.post(reverse('accounts:register'), {
            'first_name': 'Иван', 'email': 'ivan@example.com', 'birth_date': '2002-04-10',
            'password1': 'StrongPassword2026!', 'password2': 'StrongPassword2026!',
        })
        self.assertRedirects(response, reverse('articles:list'))
        user = User.objects.get(email='ivan@example.com')
        self.assertEqual(user.profile.birth_date, date(2002, 4, 10))

    def test_finance_page_requires_onboarding(self):
        user = User.objects.create_user(email='new@example.com', first_name='Новый', password='StrongPassword2026!')
        Profile.objects.update_or_create(user=user, defaults={'birth_date': date(2001, 1, 1)})
        self.client.force_login(user)
        response = self.client.get(reverse('finances:transactions'))
        self.assertRedirects(response, reverse('accounts:onboarding'))

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_password_reset_sends_working_link(self):
        User.objects.create_user(email='restore@example.com', first_name='Ирина', password='StrongPassword2026!')
        response = self.client.post(reverse('password_reset'), {'email': 'restore@example.com'})
        self.assertRedirects(response, reverse('password_reset_done'))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('/accounts/reset/', mail.outbox[0].body)

    def test_profile_rejects_future_birth_date(self):
        user = User.objects.create_user(email='profile@example.com', first_name='Ирина', password='StrongPassword2026!')
        Profile.objects.update_or_create(user=user, defaults={'birth_date': date(2000, 1, 1)})
        self.client.force_login(user)
        response = self.client.post(reverse('accounts:profile'), {
            'first_name': 'Ирина', 'birth_date': '2999-01-01', 'expected_income': '50000',
            'payday': '10', 'reserve_target': '100000',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Дата рождения должна быть в прошлом.')

    def test_email_login_is_case_insensitive(self):
        user = User.objects.create_user(email='reader@example.com', first_name='Тест', password='StrongPassword2026!')
        self.assertEqual(authenticate(username='READER@EXAMPLE.COM', password='StrongPassword2026!'), user)

    def test_authenticated_login_redirects_to_feed(self):
        user = User.objects.create_user(email='signedin@example.com', first_name='Тест')
        self.client.force_login(user)
        self.assertRedirects(self.client.get(reverse('login')), reverse('articles:list'))

    def test_password_change_page_renders(self):
        user = User.objects.create_user(email='change@example.com', first_name='Тест')
        self.client.force_login(user)
        self.assertEqual(self.client.get(reverse('password_change')).status_code, 200)

    def test_signed_in_user_can_see_password_reset_form(self):
        user = User.objects.create_user(email='signedreset@example.com', first_name='Тест')
        self.client.force_login(user)
        response = self.client.get(reverse('password_reset'))
        self.assertContains(response, 'name="email"')

    def test_registration_rejects_different_case_of_existing_email(self):
        User.objects.create_user(email='reader@example.com', first_name='Тест')
        response = self.client.post(reverse('accounts:register'), {
            'first_name': 'Иван', 'email': 'READER@example.com', 'birth_date': '2002-04-10',
            'password1': 'StrongPassword2026!', 'password2': 'StrongPassword2026!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('email', response.context['form'].errors)
        self.assertEqual(User.objects.filter(email__iexact='reader@example.com').count(), 1)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_password_reset_changes_password_and_consumes_link(self):
        import re
        user = User.objects.create_user(email='reset@example.com', first_name='Тест', password='OldPassword2026!')
        self.client.post(reverse('password_reset'), {'email': user.email})
        link = re.search(r'https?://[^\s]+', mail.outbox[0].body).group()
        response = self.client.get(link, follow=True)
        confirm_url = response.request['PATH_INFO']
        response = self.client.post(confirm_url, {
            'new_password1': 'NewPassword2026!', 'new_password2': 'NewPassword2026!',
        })
        self.assertRedirects(response, reverse('password_reset_complete'))
        user.refresh_from_db()
        self.assertTrue(user.check_password('NewPassword2026!'))
        self.assertFalse(user.check_password('OldPassword2026!'))
        response = self.client.get(link, follow=True)
        self.assertContains(response, 'Ссылка недействительна')
