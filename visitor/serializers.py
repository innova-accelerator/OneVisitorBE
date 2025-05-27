from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from .models import Visitor, PageView, Session, Event
from users.serializers import UserSerializer

class VisitorSerializer(serializers.ModelSerializer):
    """Serializer for Visitor model"""
    user = UserSerializer(read_only=True)
    last_visit_duration = serializers.DurationField(read_only=True)
    is_returning = serializers.BooleanField(read_only=True)

    class Meta:
        model = Visitor
        fields = [
            'id', 'user', 'ip_address', 'user_agent', 'referrer',
            'country', 'city', 'device_type', 'browser', 'os',
            'is_authenticated', 'first_visit', 'last_visit',
            'last_visit_duration', 'is_returning', 'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'id', 'first_visit', 'last_visit', 'created_at',
            'updated_at'
        ]

    def get_is_returning(self, obj):
        """Check if visitor is returning"""
        return obj.first_visit != obj.last_visit

class PageViewSerializer(serializers.ModelSerializer):
    """Serializer for PageView model"""
    visitor_id = serializers.UUIDField(source='visitor.id', read_only=True)
    session_id = serializers.UUIDField(source='session.id', read_only=True)
    is_bounce = serializers.BooleanField(read_only=True)

    class Meta:
        model = PageView
        fields = [
            'id', 'visitor', 'visitor_id', 'session', 'session_id',
            'url', 'path', 'title', 'duration', 'is_bounce',
            'timestamp', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'timestamp', 'created_at', 'updated_at']

    def validate(self, data):
        """Validate page view data"""
        if data.get('duration') and data['duration'].total_seconds() < 0:
            raise serializers.ValidationError(
                _("Duration cannot be negative")
            )
        return data

class SessionSerializer(serializers.ModelSerializer):
    """Serializer for Session model"""
    visitor_id = serializers.UUIDField(source='visitor.id', read_only=True)
    page_views_count = serializers.IntegerField(read_only=True)
    duration = serializers.DurationField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = Session
        fields = [
            'id', 'visitor', 'visitor_id', 'session_id', 'start_time',
            'end_time', 'duration', 'page_views_count', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'session_id', 'start_time', 'end_time',
            'created_at', 'updated_at'
        ]

    def get_page_views_count(self, obj):
        """Get count of page views in session"""
        return obj.page_views.count()

    def get_duration(self, obj):
        """Calculate session duration"""
        if obj.end_time:
            return obj.end_time - obj.start_time
        return timezone.now() - obj.start_time

class EventSerializer(serializers.ModelSerializer):
    """Serializer for Event model"""
    visitor_id = serializers.UUIDField(source='visitor.id', read_only=True)
    session_id = serializers.UUIDField(source='session.id', read_only=True)

    class Meta:
        model = Event
        fields = [
            'id', 'visitor', 'visitor_id', 'session', 'session_id',
            'event_type', 'element_id', 'element_class', 'element_text',
            'metadata', 'timestamp', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'timestamp', 'created_at', 'updated_at']

class VisitorAnalyticsSerializer(serializers.Serializer):
    """Serializer for visitor analytics"""
    visitor = VisitorSerializer()
    total_sessions = serializers.IntegerField()
    total_page_views = serializers.IntegerField()
    total_events = serializers.IntegerField()
    average_session_duration = serializers.DurationField()
    average_pages_per_session = serializers.FloatField()
    bounce_rate = serializers.FloatField()
    conversion_rate = serializers.FloatField()
    last_session = SessionSerializer()
    top_pages = serializers.ListField(
        child=serializers.DictField()
    )
    top_events = serializers.ListField(
        child=serializers.DictField()
    )

class PageViewAggregationSerializer(serializers.Serializer):
    """Serializer for page view aggregation"""
    path = serializers.CharField()
    title = serializers.CharField()
    total_views = serializers.IntegerField()
    unique_visitors = serializers.IntegerField()
    average_duration = serializers.DurationField()
    bounce_rate = serializers.FloatField()
    conversion_rate = serializers.FloatField()

class SessionAggregationSerializer(serializers.Serializer):
    """Serializer for session aggregation"""
    date = serializers.DateField()
    total_sessions = serializers.IntegerField()
    unique_visitors = serializers.IntegerField()
    average_duration = serializers.DurationField()
    average_pages_per_session = serializers.FloatField()
    bounce_rate = serializers.FloatField()

class EventAggregationSerializer(serializers.Serializer):
    """Serializer for event aggregation"""
    event_type = serializers.CharField()
    total_events = serializers.IntegerField()
    unique_visitors = serializers.IntegerField()
    average_per_session = serializers.FloatField()
    conversion_rate = serializers.FloatField()

class VisitorLocationSerializer(serializers.Serializer):
    """Serializer for visitor location data"""
    country = serializers.CharField()
    city = serializers.CharField()
    total_visitors = serializers.IntegerField()
    unique_visitors = serializers.IntegerField()
    average_session_duration = serializers.DurationField()
    conversion_rate = serializers.FloatField()

class DeviceAnalyticsSerializer(serializers.Serializer):
    """Serializer for device analytics"""
    device_type = serializers.CharField()
    browser = serializers.CharField()
    os = serializers.CharField()
    total_visitors = serializers.IntegerField()
    unique_visitors = serializers.IntegerField()
    average_session_duration = serializers.DurationField()
    bounce_rate = serializers.FloatField()
    conversion_rate = serializers.FloatField()

class VisitorTimelineSerializer(serializers.Serializer):
    """Serializer for visitor timeline"""
    timestamp = serializers.DateTimeField()
    event_type = serializers.CharField()
    page_view = PageViewSerializer(required=False)
    session = SessionSerializer(required=False)
    event = EventSerializer(required=False)
    metadata = serializers.DictField(required=False)

class VisitorJourneySerializer(serializers.Serializer):
    """Serializer for visitor journey"""
    visitor = VisitorSerializer()
    sessions = SessionSerializer(many=True)
    page_views = PageViewSerializer(many=True)
    events = EventSerializer(many=True)
    conversion_path = serializers.ListField(
        child=serializers.DictField()
    )
    total_duration = serializers.DurationField()
    engagement_score = serializers.FloatField() 