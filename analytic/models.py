from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()

class Visitor(models.Model):
    """Model to store visitor information"""
    ip_address = models.GenericIPAddressField(_("IP Address"), null=True, blank=True)
    user_agent = models.TextField(_("User Agent"), null=True, blank=True)
    referrer = models.URLField(_("Referrer"), null=True, blank=True)
    first_visit = models.DateTimeField(_("First Visit"), auto_now_add=True)
    last_visit = models.DateTimeField(_("Last Visit"), auto_now=True)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='visits',
        verbose_name=_("User")
    )
    is_authenticated = models.BooleanField(_("Is Authenticated"), default=False)
    country = models.CharField(_("Country"), max_length=100, null=True, blank=True)
    city = models.CharField(_("City"), max_length=100, null=True, blank=True)
    device_type = models.CharField(_("Device Type"), max_length=50, null=True, blank=True)
    browser = models.CharField(_("Browser"), max_length=50, null=True, blank=True)
    os = models.CharField(_("Operating System"), max_length=50, null=True, blank=True)

    class Meta:
        verbose_name = _("Visitor")
        verbose_name_plural = _("Visitors")
        ordering = ['-last_visit']

    def __str__(self):
        return f"Visitor {self.ip_address} - {self.first_visit.date()}"

class PageView(models.Model):
    """Model to track individual page views"""
    visitor = models.ForeignKey(
        Visitor,
        on_delete=models.CASCADE,
        related_name='page_views',
        verbose_name=_("Visitor")
    )
    url = models.URLField(_("URL"))
    path = models.CharField(_("Path"), max_length=255)
    title = models.CharField(_("Page Title"), max_length=255, null=True, blank=True)
    timestamp = models.DateTimeField(_("Timestamp"), auto_now_add=True)
    duration = models.IntegerField(_("Duration in seconds"), null=True, blank=True)
    is_bounce = models.BooleanField(_("Is Bounce"), default=False)

    class Meta:
        verbose_name = _("Page View")
        verbose_name_plural = _("Page Views")
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.visitor} - {self.path} - {self.timestamp}"

class Session(models.Model):
    """Model to track visitor sessions"""
    visitor = models.ForeignKey(
        Visitor,
        on_delete=models.CASCADE,
        related_name='sessions',
        verbose_name=_("Visitor")
    )
    start_time = models.DateTimeField(_("Start Time"), auto_now_add=True)
    end_time = models.DateTimeField(_("End Time"), null=True, blank=True)
    is_active = models.BooleanField(_("Is Active"), default=True)
    session_id = models.CharField(_("Session ID"), max_length=100, unique=True)
    page_views = models.ManyToManyField(
        PageView,
        related_name='sessions',
        verbose_name=_("Page Views")
    )

    class Meta:
        verbose_name = _("Session")
        verbose_name_plural = _("Sessions")
        ordering = ['-start_time']

    def __str__(self):
        return f"Session {self.session_id} - {self.visitor}"

class Event(models.Model):
    """Model to track specific events/actions"""
    EVENT_TYPES = (
        ('click', _('Click')),
        ('scroll', _('Scroll')),
        ('form_submit', _('Form Submit')),
        ('download', _('Download')),
        ('custom', _('Custom')),
    )

    visitor = models.ForeignKey(
        Visitor,
        on_delete=models.CASCADE,
        related_name='events',
        verbose_name=_("Visitor")
    )
    session = models.ForeignKey(
        Session,
        on_delete=models.CASCADE,
        related_name='events',
        verbose_name=_("Session")
    )
    event_type = models.CharField(_("Event Type"), max_length=50, choices=EVENT_TYPES)
    element_id = models.CharField(_("Element ID"), max_length=255, null=True, blank=True)
    element_class = models.CharField(_("Element Class"), max_length=255, null=True, blank=True)
    element_text = models.TextField(_("Element Text"), null=True, blank=True)
    timestamp = models.DateTimeField(_("Timestamp"), auto_now_add=True)
    metadata = models.JSONField(_("Additional Metadata"), null=True, blank=True)

    class Meta:
        verbose_name = _("Event")
        verbose_name_plural = _("Events")
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.event_type} - {self.visitor} - {self.timestamp}" 