from django.shortcuts import redirect, render


def landing(request):
    if request.user.is_authenticated:
        return redirect('articles:list')
    return render(request, 'core/landing.html')
