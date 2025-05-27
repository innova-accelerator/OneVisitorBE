from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from .models import TimeFrame, PageAnalytics, UserBehavior, Conversion, Report, Metric
from visitors.models import Visitor, PageView

User = get_user_model()

class TimeFrameSerializer(serializers.ModelSerializer):
    """Serializer for TimeFrame model"""
    class Meta:
        model = TimeFrame
        fields = [
            'id', 'name', 'start_date', 'end_date', 'granularity',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def validate(self, data):
        """Validate that end_date is after start_date"""
        if data['end_date'] <= data['start_date']:
            raise serializers.ValidationError(
                _("End date must be after start date")
            )
        return data

class PageAnalyticsSerializer(serializers.ModelSerializer):
    """Serializer for PageAnalytics model"""
    page_url = serializers.CharField(source='page_view.url', read_only=True)
    page_title = serializers.CharField(source='page_view.title', read_only=True)

    class Meta:
        model = PageAnalytics
        fields = [
            'id', 'time_frame', 'page_view', 'page_url', 'page_title',
            'total_views', 'unique_visitors', 'average_time_on_page',
            'bounce_rate', 'conversion_rate', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class UserBehaviorSerializer(serializers.ModelSerializer):
    """Serializer for UserBehavior model"""
    visitor_id = serializers.UUIDField(source='visitor.id', read_only=True)
    visitor_ip = serializers.IPAddressField(source='visitor.ip_address', read_only=True)

    class Meta:
        model = UserBehavior
        fields = [
            'id', 'visitor', 'visitor_id', 'visitor_ip', 'time_frame',
            'average_session_duration', 'pages_per_session', 'return_rate',
            'engagement_score', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class ConversionSerializer(serializers.ModelSerializer):
    """Serializer for Conversion model"""
    visitor_id = serializers.UUIDField(source='visitor.id', read_only=True)
    visitor_ip = serializers.IPAddressField(source='visitor.ip_address', read_only=True)

    class Meta:
        model = Conversion
        fields = [
            'id', 'visitor', 'visitor_id', 'visitor_ip', 'conversion_type',
            'value', 'timestamp', 'metadata', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class ReportSerializer(serializers.ModelSerializer):
    """Serializer for Report model"""
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True)
    time_frame_name = serializers.CharField(source='time_frame.name', read_only=True)

    class Meta:
        model = Report
        fields = [
            'id', 'name', 'description', 'report_type', 'time_frame',
            'time_frame_name', 'data', 'created_by', 'created_by_email',
            'last_generated', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'last_generated']

    def validate_report_type(self, value):
        """Validate report type"""
        valid_types = ['visitor', 'page', 'conversion', 'custom']
        if value not in valid_types:
            raise serializers.ValidationError(
                _("Invalid report type. Must be one of: %(types)s"),
                params={'types': ', '.join(valid_types)}
            )
        return value

class MetricSerializer(serializers.ModelSerializer):
    """Serializer for Metric model"""
    class Meta:
        model = Metric
        fields = [
            'id', 'name', 'description', 'formula', 'unit',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def validate_formula(self, value):
        """Validate metric formula"""
        # Add formula validation logic here
        # This could include checking for valid operators, fields, etc.
        return value

class AnalyticsSummarySerializer(serializers.Serializer):
    """Serializer for analytics summary"""
    time_frame = serializers.CharField()
    start_date = serializers.DateTimeField()
    end_date = serializers.DateTimeField()
    
    visitor_metrics = serializers.DictField(
        child=serializers.IntegerField()
    )
    
    page_metrics = serializers.DictField(
        child=serializers.FloatField()
    )
    
    conversion_metrics = serializers.DictField(
        child=serializers.FloatField()
    )

    def validate(self, data):
        """Validate summary data"""
        if data['end_date'] <= data['start_date']:
            raise serializers.ValidationError(
                _("End date must be after start date")
            )
        return data

class PageViewAggregationSerializer(serializers.Serializer):
    """Serializer for page view aggregation"""
    period = serializers.DateTimeField()
    total_views = serializers.IntegerField()
    unique_visitors = serializers.IntegerField()
    avg_time = serializers.FloatField()
    bounce_rate = serializers.FloatField()
    conversion_rate = serializers.FloatField()

class ConversionMetricsSerializer(serializers.Serializer):
    """Serializer for conversion metrics"""
    conversion_type = serializers.CharField()
    count = serializers.IntegerField()
    total_value = serializers.FloatField()

class VisitorReportSerializer(serializers.Serializer):
    """Serializer for visitor report data"""
    total_visitors = serializers.IntegerField()
    new_visitors = serializers.IntegerField()
    returning_visitors = serializers.IntegerField()
    authenticated_visitors = serializers.IntegerField()
    
    visitor_locations = serializers.ListField(
        child=serializers.DictField(
            child=serializers.IntegerField()
        )
    )
    
    device_types = serializers.ListField(
        child=serializers.DictField(
            child=serializers.IntegerField()
        )
    )
    
    browsers = serializers.ListField(
        child=serializers.DictField(
            child=serializers.IntegerField()
        )
    )
    
    operating_systems = serializers.ListField(
        child=serializers.DictField(
            child=serializers.IntegerField()
        )
    )

class PageReportSerializer(serializers.Serializer):
    """Serializer for page report data"""
    total_page_views = serializers.IntegerField()
    unique_pages = serializers.IntegerField()
    average_time_on_page = serializers.FloatField()
    bounce_rate = serializers.FloatField()
    
    top_pages = serializers.ListField(
        child=serializers.DictField(
            child=serializers.FloatField()
        )
    )

class ConversionReportSerializer(serializers.Serializer):
    """Serializer for conversion report data"""
    total_conversions = serializers.IntegerField()
    conversion_value = serializers.FloatField()
    conversion_rate = serializers.FloatField()
    
    conversion_types = serializers.ListField(
        child=serializers.DictField(
            child=serializers.FloatField()
        )
    ) 