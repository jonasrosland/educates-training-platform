import json
import enum
import datetime

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

from oauth2_provider.models import Application


User = get_user_model()


class SingletonModel(models.Model):
    class Meta:
        abstract = True

    def save(self, *args, **kwargs): # pylint: disable=signature-differs
        self.pk = 1
        super(SingletonModel, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs): # pylint: disable=signature-differs
        pass

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1) # pylint: disable=unused-variable
        return obj


class JSONField(models.Field):
    def db_type(self, connection):
        return "text"

    def from_db_value(self, value, expression, connection): # pylint: disable=unused-argument
        if value is not None:
            return self.to_python(value)
        return value

    def to_python(self, value):
        if value is not None:
            try:
                return json.loads(value)
            except (TypeError, ValueError):
                return value
        return value

    def get_prep_value(self, value):
        if value is not None:
            return str(json.dumps(value))
        return value

    def value_to_string(self, obj):
        return self.value_from_object(obj)


class TrainingPortal(SingletonModel):
    sessions_maximum = models.IntegerField(verbose_name="sessions maximum", default=0)
    sessions_registered = models.IntegerField(
        verbose_name="sessions registered", default=0
    )
    sessions_anonymous = models.IntegerField(
        verbose_name="sessions anonymous", default=0
    )


class Workshop(models.Model):
    name = models.CharField(
        verbose_name="workshop name", max_length=255, primary_key=True
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    vendor = models.CharField(max_length=128)
    authors = JSONField(default=[])
    difficulty = models.CharField(max_length=128)
    duration = models.CharField(max_length=128)
    tags = JSONField(default=[])
    logo = models.TextField()
    url = models.CharField(max_length=255)
    content = JSONField(default={})


class Environment(models.Model):
    name = models.CharField(
        verbose_name="environment name", max_length=256, primary_key=True
    )
    workshop = models.ForeignKey(Workshop, on_delete=models.PROTECT)
    capacity = models.IntegerField(verbose_name="maximum capacity", default=0)
    initial = models.IntegerField(verbose_name="initial instances", default=0)
    reserved = models.IntegerField(verbose_name="reserved instances", default=0)
    duration = models.DurationField(verbose_name="workshop duration", default=0)
    inactivity = models.DurationField(verbose_name="inactivity timeout", default=0)
    tally = models.IntegerField(verbose_name="workshop tally", default=0)
    resource = JSONField(verbose_name="resource definition", default={})

    def workshop_name(self):
        return self.workshop.name

    workshop_name.admin_order_field = "workshop__name"

    def available_sessions(self):
        return self.session_set.filter(
            owner__isnull=True, state__in=(SessionState.STARTING, SessionState.WAITING)
        )

    def available_session(self):
        sessions = self.available_sessions()
        return sessions and sessions[0] or None

    def available_sessions_count(self):
        return self.available_sessions().count()

    available_sessions_count.short_description = "Available"

    def allocated_sessions(self):
        return self.session_set.filter(
            state__in=(
                SessionState.STARTING,
                SessionState.WAITING,
                SessionState.RUNNING,
                SessionState.STOPPING,
            )
        ).exclude(owner__isnull=True)

    def allocated_sessions_count(self):
        return self.allocated_sessions().count()

    allocated_sessions_count.short_description = "Allocated"

    def allocated_session_for_user(self, user):
        sessions = self.session_set.filter(
            state__in=(
                SessionState.STARTING,
                SessionState.WAITING,
                SessionState.RUNNING,
                SessionState.STOPPING,
            ),
            owner=user,
        )
        if sessions:
            return sessions[0]

    def active_sessions(self):
        return self.session_set.filter(
            state__in=(
                SessionState.STARTING,
                SessionState.WAITING,
                SessionState.RUNNING,
                SessionState.STOPPING,
            )
        )

    def active_sessions_count(self):
        return self.active_sessions().count()

    active_sessions_count.short_description = "Active"


class SessionState(enum.IntEnum):
    STARTING = 1
    WAITING = 2
    RUNNING = 3
    STOPPING = 4
    STOPPED = 5

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]


class Session(models.Model):
    name = models.CharField(
        verbose_name="session name", max_length=256, primary_key=True
    )
    id = models.CharField(max_length=64)
    application = models.ForeignKey(
        Application, blank=True, null=True, on_delete=models.PROTECT
    )
    state = models.IntegerField(
        choices=SessionState.choices(), default=SessionState.STARTING
    )
    owner = models.ForeignKey(User, blank=True, null=True, on_delete=models.PROTECT)
    created = models.DateTimeField(null=True, blank=True)
    started = models.DateTimeField(null=True, blank=True)
    expires = models.DateTimeField(null=True, blank=True)
    token = models.CharField(max_length=256, null=True, blank=True)
    environment = models.ForeignKey(Environment, on_delete=models.PROTECT)

    def environment_name(self):
        return self.environment.name

    environment_name.admin_order_field = "environment__name"

    def workshop_name(self):
        return self.environment.workshop.name

    workshop_name.admin_order_field = "environment__workshop__name"

    def is_available(self):
        return self.owner is None and self.state in (
            SessionState.STARTING,
            SessionState.WAITING,
        )

    is_available.short_description = "Available"
    is_available.boolean = True

    def is_pending(self):
        return self.owner and self.state in (
            SessionState.STARTING,
            SessionState.WAITING,
        )

    is_pending.short_description = "Pending"
    is_pending.boolean = True

    def is_allocated(self):
        return self.owner is not None and self.state != SessionState.STOPPED

    is_allocated.short_description = "Allocated"
    is_allocated.boolean = True

    def is_running(self):
        return self.state == SessionState.RUNNING

    is_running.short_description = "Running"
    is_running.boolean = True

    def is_stopping(self):
        return self.state == SessionState.STOPPING

    is_stopping.short_description = "Stopping"
    is_stopping.boolean = True

    def is_stopped(self):
        return self.state == SessionState.STOPPED

    is_stopped.short_description = "Stopped"
    is_stopped.boolean = True

    def remaining_time(self):
        now = timezone.now()
        if self.is_allocated() and self.expires:
            if now >= self.expires:
                return 0

            return (self.expires - now).total_seconds()

    def remaining_time_as_string(self):
        remaining = self.remaining_time()
        if remaining is not None:
            return "%02d:%02d" % (remaining / 60, remaining % 60)

    remaining_time_as_string.short_description = "Remaining"

    def mark_as_pending(self, user, token=None):
        self.owner = user
        self.started = timezone.now()
        self.token = self.token or token
        if token:
            self.expires = self.started + datetime.timedelta(seconds=60)
        elif self.environment.duration:
            self.expires = self.started + self.environment.duration
        self.save()
        return self

    def mark_as_running(self, user=None):
        self.owner = user or self.owner
        self.state = SessionState.RUNNING
        self.started = timezone.now()
        if self.environment.duration:
            self.expires = self.started + self.environment.duration
        else:
            self.expires = None
        self.save()
        return self

    def mark_as_stopping(self):
        self.state = SessionState.STOPPING
        self.expires = timezone.now()
        self.save()

    def mark_as_stopped(self):
        application = self.application
        self.state = SessionState.STOPPED
        self.expires = timezone.now()
        self.application = None
        self.save()
        application.delete()

    def extend_time_remaining(self, period=300):
        if self.expires and self.state == SessionState.RUNNING:
            now = timezone.now()
            remaining = (self.expires - now).total_seconds()
            if remaining > 0 and remaining <= period:
                self.expires = self.expires + datetime.timedelta(seconds=300)
                self.save()

    def time_remaining(self):
        if self.expires:
            now = timezone.now()
            if self.expires > now:
                return int((self.expires - now).total_seconds())
            return 0

    @staticmethod
    def allocated_session(name, user=None):
        try:
            session = Session.objects.get(
                name=name,
                state__in=(
                    SessionState.STARTING,
                    SessionState.WAITING,
                    SessionState.RUNNING,
                    SessionState.STOPPING,
                ),
            )
            if user:
                if session.owner == user:
                    return session
            else:
                return session
        except Session.DoesNotExist:
            pass

    @staticmethod
    def allocated_sessions():
        return Session.objects.exclude(owner__isnull=True).exclude(
            state=SessionState.STOPPED
        )

    @staticmethod
    def allocated_sessions_for_user(user):
        return Session.objects.filter(owner=user).exclude(state=SessionState.STOPPED)

    @staticmethod
    def available_sessions():
        return Session.objects.filter(
            owner__isnull=True, state__in=(SessionState.STARTING, SessionState.WAITING)
        )