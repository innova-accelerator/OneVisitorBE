from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Visitor(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    referrer = models.URLField(max_length=500, blank=True)
    country = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    device_type = models.CharField(max_length=50)
    browser = models.CharField(max_length=50)
    os = models.CharField(max_length=50)
    is_authenticated = models.BooleanField(default=False)
    first_visit = models.DateTimeField(auto_now_add=True)
    last_visit = models.DateTimeField(auto_now=True)
    last_visit_duration = models.DurationField(null=True, blank=True)
    is_returning = models.BooleanField(default=False)
    site = models.ForeignKey('sites.Site', on_delete=models.CASCADE, related_name='visitors')

    class Meta:
        indexes = [
            models.Index(fields=['ip_address']),
            models.Index(fields=['user']),
            models.Index(fields=['first_visit']),
        ]

class Session(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    visitor = models.ForeignKey(Visitor, on_delete=models.CASCADE, related_name='sessions')
    session_id = models.CharField(max_length=100, unique=True)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    duration = models.DurationField(null=True, blank=True)
    page_views_count = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    site = models.ForeignKey('sites.Site', on_delete=models.CASCADE, related_name='visitors')

    class Meta:
        indexes = [
            models.Index(fields=['visitor', 'start_time']),
            models.Index(fields=['session_id']),
        ]

class PageView(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    visitor = models.ForeignKey(Visitor, on_delete=models.CASCADE, related_name='page_views')
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='page_views')
    url = models.URLField(max_length=500)
    path = models.CharField(max_length=500)
    title = models.CharField(max_length=200)
    duration = models.DurationField(null=True, blank=True)
    is_bounce = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    site = models.ForeignKey('sites.Site', on_delete=models.CASCADE, related_name='visitors')

    class Meta:
        indexes = [
            models.Index(fields=['visitor', 'timestamp']),
            models.Index(fields=['session', 'timestamp']),
            models.Index(fields=['path']),
        ]

class Event(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    visitor = models.ForeignKey(Visitor, on_delete=models.CASCADE, related_name='events')
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='events')
    event_type = models.CharField(max_length=100)
    element_id = models.CharField(max_length=100, blank=True)
    element_class = models.CharField(max_length=200, blank=True)
    element_text = models.TextField(blank=True)
    metadata = models.JSONField(default=dict)
    timestamp = models.DateTimeField(auto_now_add=True)
    site = models.ForeignKey('sites.Site', on_delete=models.CASCADE, related_name='visitors')

    class Meta:
        indexes = [
            models.Index(fields=['visitor', 'timestamp']),
            models.Index(fields=['session', 'timestamp']),
            models.Index(fields=['event_type']),
        ]