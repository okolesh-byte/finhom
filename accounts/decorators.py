from functools import wraps

from django.shortcuts import redirect

from .models import Profile


def onboarding_required(view_func):
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        if not profile.onboarding_completed:
            return redirect('accounts:onboarding')
        return view_func(request, *args, **kwargs)

    return wrapped
