from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()

class TimeFrame(models.Model):
    """Model for managing time periods for analytics"""
    name = models.CharField(_("Name"), max_length=100)
    start_date = models.DateTimeField(_("Start Date"))
    end_date = models.DateTimeField(_("End Date"))
    granularity = models.CharField(_("Granularity"), max_length=20, choices=[
        ('hourly', _('Hourly')),
        ('daily', _('Daily')),
        ('weekly', _('Weekly')),
        ('monthly', _('Monthly'))
    ])
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        verbose_name = _("Time Frame")
        verbose_name_plural = _("Time Frames")
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.name} ({self.start_date.date()} - {self.end_date.date()})"

class PageAnalytics(models.Model):
    """Model for storing aggregated page analytics data"""
    time_frame = models.ForeignKey(
        TimeFrame,
        on_delete=models.CASCADE,
        related_name='page_analytics',
        verbose_name=_("Time Frame")
    )
    page_view = models.ForeignKey(
        'visitors.PageView',
        on_delete=models.CASCADE,
        related_name='analytics',
        verbose_name=_("Page View")
    )
    total_views = models.IntegerField(_("Total Views"), default=0)
    unique_visitors = models.IntegerField(_("Unique Visitors"), default=0)
    average_time_on_page = models.FloatField(_("Average Time on Page"), default=0)
    bounce_rate = models.FloatField(_("Bounce Rate"), default=0)
    conversion_rate = models.FloatField(_("Conversion Rate"), default=0)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        verbose_name = _("Page Analytics")
        verbose_name_plural = _("Page Analytics")
        ordering = ['-time_frame__start_date']

    def __str__(self):
        return f"Analytics for {self.page_view.path} - {self.time_frame}"

class UserBehavior(models.Model):
    """Model for tracking user behavior patterns"""
    visitor = models.ForeignKey(
        'visitors.Visitor',
        on_delete=models.CASCADE,
        related_name='behaviors',
        verbose_name=_("Visitor")
    )
    time_frame = models.ForeignKey(
        TimeFrame,
        on_delete=models.CASCADE,
        related_name='user_behaviors',
        verbose_name=_("Time Frame")
    )
    average_session_duration = models.DurationField(_("Average Session Duration"), null=True)
    pages_per_session = models.FloatField(_("Pages per Session"), default=0)
    return_rate = models.FloatField(_("Return Rate"), default=0)
    engagement_score = models.FloatField(_("Engagement Score"), default=0)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        verbose_name = _("User Behavior")
        verbose_name_plural = _("User Behaviors")
        ordering = ['-time_frame__start_date']

    def __str__(self):
        return f"Behavior for {self.visitor} - {self.time_frame}"

class Conversion(models.Model):
    """Model for tracking conversion events"""
    visitor = models.ForeignKey(
        'visitors.Visitor',
        on_delete=models.CASCADE,
        related_name='conversions',
        verbose_name=_("Visitor")
    )
    conversion_type = models.CharField(_("Conversion Type"), max_length=50)
    value = models.FloatField(_("Value"), default=0)
    timestamp = models.DateTimeField(_("Timestamp"), auto_now_add=True)
    metadata = models.JSONField(_("Additional Metadata"), null=True, blank=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        verbose_name = _("Conversion")
        verbose_name_plural = _("Conversions")
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.conversion_type} - {self.visitor} - {self.timestamp}"

class Report(models.Model):
    """Model for storing generated reports"""
    name = models.CharField(_("Name"), max_length=100)
    report_type = models.CharField(_("Report Type"), max_length=50, choices=[
        ('visitor', _('Visitor')),
        ('page', _('Page')),
        ('conversion', _('Conversion')),
        ('custom', _('Custom'))
    ])
    time_frame = models.ForeignKey(
        TimeFrame,
        on_delete=models.CASCADE,
        related_name='reports',
        verbose_name=_("Time Frame")
    )
    data = models.JSONField(_("Report Data"), default=dict)
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reports',
        verbose_name=_("Created By")
    )
    last_generated = models.DateTimeField(_("Last Generated"), null=True, blank=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        verbose_name = _("Report")
        verbose_name_plural = _("Reports")
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.report_type}"

class Metric(models.Model):
    """Model for custom metrics"""
    name = models.CharField(_("Name"), max_length=100)
    description = models.TextField(_("Description"))
    is_active = models.BooleanField(_("Is Active"), default=True)
    configuration = models.JSONField(_("Configuration"), default=dict)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        verbose_name = _("Metric")
        verbose_name_plural = _("Metrics")
        ordering = ['name']

    def __str__(self):
        return self.name 