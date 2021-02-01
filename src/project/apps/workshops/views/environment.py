"""Defines view handlers for working with environments via the web interface.

"""

__all__ = ["environment", "environment_create", "environment_request"]

import uuid
import string
import random

from django.shortcuts import redirect, reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from django.http import HttpResponseForbidden, HttpResponseBadRequest
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.utils.http import urlencode
from django.http import JsonResponse
from django.db import transaction
from django.contrib.auth import login
from django.conf import settings

from oauth2_provider.decorators import protected_resource

from ..manager.sessions import retrieve_session_for_user
from ..manager.locking import resources_lock
from ..models import Environment


@login_required
@resources_lock
@transaction.atomic
def environment(request, name):
    """Initiate creation of a workshop session against the specific workshop
    environment.

    """

    index_url = request.session.get("index_url")

    # Ensure there is an environment with the specified name in existance.

    try:
        instance = Environment.objects.get(name=name)
    except Environment.DoesNotExist:
        if index_url:
            return redirect(index_url + "?notification=workshop-invalid")

        if not request.user.is_staff and settings.PORTAL_INDEX:
            return redirect(settings.PORTAL_INDEX + "?notification=workshop-invalid")

        return redirect(reverse("workshops_catalog") + "?notification=workshop-invalid")

    # Retrieve a session for the user for this workshop environment.

    session = retrieve_session_for_user(instance, request.user)

    if session:
        return redirect("workshops_session", name=session.name)

    if index_url:
        return redirect(index_url + "?notification=session-unavailable")

    if not request.user.is_staff and settings.PORTAL_INDEX:
        return redirect(settings.PORTAL_INDEX + "?notification=session-unavailable")

    return redirect(reverse("workshops_catalog") + "?notification=session-unavailable")


@resources_lock
@transaction.atomic
def environment_create(request, name):
    """Direct URL that can be used to create workshop sessions. Will redirect
    to login page if necessary, otherwise redirects to the view handler that
    triggers the actual creation of the workshop session for the specified
    workshop environment.

    """

    # Where the user is already authenticated, redirect immediately to
    # endpoint which actually triggers creation of environment. It will
    # validate if it is a correct environment name.

    if request.user.is_authenticated:
        return redirect("workshops_environment", name)

    # Where anonymous access is not enabled, need to redirect back to the
    # login page and they will need to first login.

    if (
        settings.ENABLE_REGISTRATION != "true"
        or settings.REGISTRATION_TYPE != "anonymous"
    ):
        return redirect("login")

    # Is anonymous access, so we can login the user automatically.

    created = False

    User = get_user_model()  # pylint: disable=invalid-name

    while not created:
        username = f"anon@eduk8s:{uuid.uuid4()}"
        user, created = User.objects.get_or_create(username=username)

    group, _ = Group.objects.get_or_create(name="anonymous")

    user.groups.add(group)

    login(request, user, backend=settings.AUTHENTICATION_BACKENDS[0])

    # Finally redirect to endpoint which actually triggers creation of
    # environment. It will validate if it is a correct environment name.

    index_url = request.GET.get("index_url")

    request.session["index_url"] = index_url

    return redirect(reverse("workshops_environment", args=(name,)))


@protected_resource()
@resources_lock
@transaction.atomic
def environment_request(request, name):
    """URL for requesting creation of a workshop session against a specific
    workshop environment, via the REST API.

    """

    # Only allow user who is in the robots group to request session.

    if not request.user.groups.filter(name="robots").exists():
        return HttpResponseForbidden("Session requests not permitted")

    # Ensure there is an environment which the specified name in existance.

    try:
        instance = Environment.objects.get(name=name)
    except Environment.DoesNotExist:
        return HttpResponseForbidden("Environment does not exist")

    # Extract required parameters for creating the session. Check against
    # redirect_url, firstname and lastname is for backward compatibility
    # and will be removed in the future.

    index_url = request.GET.get("index_url")

    if not index_url:
        index_url = request.GET.get("redirect_url")

    if not index_url:
        return HttpResponseBadRequest("Need redirect URL for workshop index")

    user_id = request.GET.get("user", "").strip()

    if not user_id:
        user_id = uuid.uuid4()

    username = f"user@eduk8s:{user_id}"

    email = request.GET.get("email", "").strip()

    if email:
        try:
            validate_email(email)
        except ValidationError:
            return HttpResponseBadRequest("Invalid email address provided")

    first_name = request.GET.get("first_name", "").strip()
    last_name = request.GET.get("last_name", "").strip()

    if not first_name:
        first_name = request.GET.get("firstname", "").strip()

    if not last_name:
        last_name = request.GET.get("lastname", "").strip()

    user_details = {}

    if email:
        user_details["email"] = email

    if first_name:
        user_details["first_name"] = first_name

    if last_name:
        user_details["last_name"] = last_name

    # Check whether a user already has an existing session allocated
    # to them, in which case return that rather than create a new one.

    session = None

    User = get_user_model()  # pylint: disable=invalid-name

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        user = User.objects.create_user(username, **user_details)
        group, _ = Group.objects.get_or_create(name="anonymous")
        user.groups.add(group)
        user.save()

    # Retrieve a session for the user for this workshop environment.

    characters = string.ascii_letters + string.digits
    token = "".join(random.sample(characters, 32))

    session = retrieve_session_for_user(instance, user, token)

    if not session:
        return JsonResponse({"error": "No session available"}, status=503)

    details = {}

    details["name"] = session.name

    # The "session" property was replaced by "name" and "session" deprecated.
    # Include "session" for now, but it will be removed in future update.

    details["session"] = session.name

    details["user"] = user.username.split("user@eduk8s:")[-1]

    details["url"] = (
        reverse("workshops_session_activate", args=(session.name,))
        + "?"
        + urlencode({"token": session.token, "index_url": index_url})
    )

    # The session namespace currently has the same name as the session. Return
    # it as a separate value in case it could be different in the future.

    details["namespace"] = session.name

    details["workshop"] = session.workshop_name()
    details["environment"] = session.environment_name()

    return JsonResponse(details)