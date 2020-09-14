__all__ = ["access"]

from django.shortcuts import render, redirect
from django.conf import settings

from ..forms import AccessTokenForm


def access(request):
    if request.method == "POST":
        form = AccessTokenForm(request.POST)
        if form.is_valid():
            password = form.cleaned_data["password"]
            redirect_url = form.cleaned_data["redirect_url"]
            if settings.PORTAL_PASSWORD == password:
                request.session["is_allowed_access_to_event"] = True
                return redirect(redirect_url)
    else:
        redirect_url = request.GET.get("redirect_url")

        if not redirect_url:
            return HttpResponseBadRequest("Need redirect URL for access check")

        data = {"redirect_url": redirect_url}
        form = AccessTokenForm(initial=data)

    return render(request, "workshops/access.html", {"form": form})