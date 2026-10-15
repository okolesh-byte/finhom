from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import OnboardingForm, ProfileForm, RegistrationForm
from .models import Profile


def register(request):
    if request.user.is_authenticated:
        return redirect('articles:list')
    form = RegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        profile, _ = Profile.objects.get_or_create(user=user)
        profile.birth_date = form.cleaned_data['birth_date']
        profile.save(update_fields=['birth_date'])
        login(request, user)
        messages.success(request, 'Добро пожаловать в Finhom!')
        return redirect('articles:list')
    return render(request, 'accounts/register.html', {'form': form})


@login_required
def onboarding(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    form = OnboardingForm(request.POST or None, instance=profile)
    if request.method == 'POST' and form.is_valid():
        profile = form.save(commit=False)
        profile.onboarding_completed = True
        profile.save()
        messages.success(request, 'Настройка завершена. Теперь финансовые разделы открыты.')
        return redirect('analytics:dashboard')
    return render(request, 'accounts/onboarding.html', {'form': form})


@login_required
def profile(request):
    profile_obj, _ = Profile.objects.get_or_create(user=request.user)
    form = ProfileForm(request.POST or None, request.FILES or None, instance=profile_obj, initial={'first_name': request.user.first_name})
    if request.method == 'POST' and form.is_valid():
        profile_obj = form.save()
        request.user.first_name = form.cleaned_data['first_name']
        request.user.save(update_fields=['first_name'])
        messages.success(request, 'Профиль обновлён.')
        return redirect('accounts:profile')
    return render(request, 'accounts/profile.html', {'form': form, 'profile': profile_obj})
