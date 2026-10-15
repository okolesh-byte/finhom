from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils import timezone

from .models import Profile, User


class RegistrationForm(UserCreationForm):
    birth_date = forms.DateField(label='Дата рождения', widget=forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}))

    class Meta:
        model = User
        fields = ('first_name', 'email', 'birth_date', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Аккаунт с такой электронной почтой уже существует.')
        return email

    def clean_birth_date(self):
        value = self.cleaned_data['birth_date']
        if value >= timezone.localdate():
            raise forms.ValidationError('Дата рождения должна быть в прошлом.')
        return value


class OnboardingForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('expected_income', 'payday', 'reserve_target')
        widgets = {'payday': forms.NumberInput(attrs={'min': 1, 'max': 31})}

    def clean_payday(self):
        value = self.cleaned_data['payday']
        if not 1 <= value <= 31:
            raise forms.ValidationError('Укажите день от 1 до 31.')
        return value

    def clean_expected_income(self):
        value = self.cleaned_data['expected_income']
        if value <= 0:
            raise forms.ValidationError('Доход должен быть больше нуля.')
        return value

    def clean_reserve_target(self):
        value = self.cleaned_data['reserve_target']
        if value < 0:
            raise forms.ValidationError('Сумма резерва не может быть отрицательной.')
        return value


class ProfileForm(forms.ModelForm):
    first_name = forms.CharField(label='Имя', max_length=100)
    birth_date = forms.DateField(label='Дата рождения', widget=forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}))

    class Meta:
        model = Profile
        fields = ('first_name', 'birth_date', 'avatar', 'expected_income', 'payday', 'reserve_target')
        widgets = {
            'birth_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            'payday': forms.NumberInput(attrs={'min': 1, 'max': 31}),
        }

    def clean_birth_date(self):
        value = self.cleaned_data['birth_date']
        if value >= timezone.localdate():
            raise forms.ValidationError('Дата рождения должна быть в прошлом.')
        return value

    def clean_payday(self):
        value = self.cleaned_data['payday']
        if not 1 <= value <= 31:
            raise forms.ValidationError('Укажите день от 1 до 31.')
        return value

    def clean_expected_income(self):
        value = self.cleaned_data['expected_income']
        if value < 0:
            raise forms.ValidationError('Доход не может быть отрицательным.')
        return value

    def clean_reserve_target(self):
        value = self.cleaned_data['reserve_target']
        if value < 0:
            raise forms.ValidationError('Сумма резерва не может быть отрицательной.')
        return value

    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')
        if avatar and avatar.size > 5 * 1024 * 1024:
            raise forms.ValidationError('Размер фотографии не должен превышать 5 МБ.')
        return avatar
