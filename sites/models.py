from django.db import models
from django.conf import settings
import uuid

class Site(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    domain = models.CharField(max_length=255, unique=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sites')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    tracking_code = models.CharField(max_length=50, unique=True)  # For frontend tracking script
    settings = models.JSONField(default=dict)  # Store site-specific settings

    class Meta:
        indexes = [
            models.Index(fields=['domain']),
            models.Index(fields=['owner']),
            models.Index(fields=['tracking_code']),
        ]

    def __str__(self):
        return self.name

class SiteMember(models.Model):
    ROLE_CHOICES = (
        ('owner', 'Owner'),
        ('admin', 'Admin'),
        ('viewer', 'Viewer'),
    )

    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='site_memberships')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='viewer')
    joined_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('site', 'user')
        indexes = [
            models.Index(fields=['site', 'user']),
            models.Index(fields=['role']),
        ]

class SiteDomain(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='domains')
    domain = models.CharField(max_length=255, unique=True)
    is_primary = models.BooleanField(default=False)
    verified = models.BooleanField(default=False)
    verification_code = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['domain']),
            models.Index(fields=['site', 'is_primary']),
        ]

class SiteSettings(models.Model):
    site = models.OneToOneField(Site, on_delete=models.CASCADE, related_name='site_settings')
    tracking_enabled = models.BooleanField(default=True)
    ip_tracking = models.BooleanField(default=True)
    cookie_consent = models.BooleanField(default=True)
    data_retention_days = models.IntegerField(default=90)
    custom_domains = models.JSONField(default=list)
    excluded_paths = models.JSONField(default=list)
    included_paths = models.JSONField(default=list)
    custom_events = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['site']),
        ]