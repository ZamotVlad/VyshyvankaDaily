from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import ProfileForm


@login_required
def profile_settings_view(request):
    profile = request.user.profile
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Профіль оновлено.")
            return redirect("accounts:profile_settings")
    else:
        form = ProfileForm(instance=profile)
    return render(request, "accounts/profile_settings.html", {"form": form})
