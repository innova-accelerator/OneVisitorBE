from django.utils import timezone
from django.db.models import Count, Avg, Sum, F, Q
from django.db.models.functions import TruncDate, TruncHour, TruncDay, TruncWeek, TruncMonth
from rest_framework import viewsets, status, generics, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
import json
from datetime import timedelta

from .models import TimeFrame, PageAnalytics, UserBehavior, Conversion, Report, Metric
from visitors.models import Visitor, PageView, Session, Event
from .serializers import (
    TimeFrameSerializer,
    PageAnalyticsSerializer,
    UserBehaviorSerializer,
    ConversionSerializer,
    ReportSerializer,
    MetricSerializer,
    AnalyticsSummarySerializer,
)

User = get_user_model()

class TimeFrameViewSet(viewsets.ModelViewSet):
    """ViewSet for time frame management"""
    queryset = TimeFrame.objects.all()
    serializer_class = TimeFrameSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return TimeFrame.objects.all()
        return TimeFrame.objects.filter(
            start_date__lte=timezone.now(),
            end_date__gte=timezone.now()
        )

class PageAnalyticsViewSet(viewsets.ModelViewSet):
    """ViewSet for page analytics"""
    queryset = PageAnalytics.objects.all()
    serializer_class = PageAnalyticsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return PageAnalytics.objects.all()
        return PageAnalytics.objects.filter(
            page_view__visitor__user=self.request.user
        )

    @action(detail=False, methods=['get'])
    def aggregate(self, request):
        """Get aggregated page analytics"""
        time_frame = request.query_params.get('time_frame', 'daily')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        if not start_date or not end_date:
            end_date = timezone.now()
            start_date = end_date - timedelta(days=30)

        queryset = self.get_queryset().filter(
            time_frame__start_date__gte=start_date,
            time_frame__end_date__lte=end_date
        )

        if time_frame == 'hourly':
            trunc_func = TruncHour
        elif time_frame == 'daily':
            trunc_func = TruncDay
        elif time_frame == 'weekly':
            trunc_func = TruncWeek
        else:
            trunc_func = TruncMonth

        aggregated_data = queryset.annotate(
            period=trunc_func('time_frame__start_date')
        ).values('period').annotate(
            total_views=Sum('total_views'),
            unique_visitors=Sum('unique_visitors'),
            avg_time=Avg('average_time_on_page'),
            bounce_rate=Avg('bounce_rate'),
            conversion_rate=Avg('conversion_rate')
        ).order_by('period')

        return Response(aggregated_data)

class UserBehaviorViewSet(viewsets.ModelViewSet):
    """ViewSet for user behavior analytics"""
    queryset = UserBehavior.objects.all()
    serializer_class = UserBehaviorSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return UserBehavior.objects.all()
        return UserBehavior.objects.filter(visitor__user=self.request.user)

    @action(detail=False, methods=['get'])
    def engagement_metrics(self, request):
        """Get user engagement metrics"""
        time_frame = request.query_params.get('time_frame', 'daily')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        if not start_date or not end_date:
            end_date = timezone.now()
            start_date = end_date - timedelta(days=30)

        queryset = self.get_queryset().filter(
            time_frame__start_date__gte=start_date,
            time_frame__end_date__lte=end_date
        )

        metrics = queryset.aggregate(
            avg_session_duration=Avg('average_session_duration'),
            avg_pages_per_session=Avg('pages_per_session'),
            avg_return_rate=Avg('return_rate'),
            avg_engagement_score=Avg('engagement_score')
        )

        return Response(metrics)

class ConversionViewSet(viewsets.ModelViewSet):
    """ViewSet for conversion tracking"""
    queryset = Conversion.objects.all()
    serializer_class = ConversionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Conversion.objects.all()
        return Conversion.objects.filter(visitor__user=self.request.user)

    @action(detail=False, methods=['get'])
    def conversion_metrics(self, request):
        """Get conversion metrics"""
        time_frame = request.query_params.get('time_frame', 'daily')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        if not start_date or not end_date:
            end_date = timezone.now()
            start_date = end_date - timedelta(days=30)

        queryset = self.get_queryset().filter(
            timestamp__gte=start_date,
            timestamp__lte=end_date
        )

        metrics = queryset.values('conversion_type').annotate(
            count=Count('id'),
            total_value=Sum('value')
        ).order_by('-count')

        return Response(metrics)

class ReportViewSet(viewsets.ModelViewSet):
    """ViewSet for report management"""
    queryset = Report.objects.all()
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Report.objects.all()
        return Report.objects.filter(created_by=self.request.user)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def generate(self, request, pk=None):
        """Generate a new report"""
        report = self.get_object()
        time_frame = report.time_frame
        report_type = report.report_type

        if report_type == 'visitor':
            data = self.generate_visitor_report(time_frame)
        elif report_type == 'page':
            data = self.generate_page_report(time_frame)
        elif report_type == 'conversion':
            data = self.generate_conversion_report(time_frame)
        else:
            data = self.generate_custom_report(time_frame, report.data)

        report.data = data
        report.last_generated = timezone.now()
        report.save()

        return Response(ReportSerializer(report).data)

    def generate_visitor_report(self, time_frame):
        """Generate visitor report data"""
        visitors = Visitor.objects.filter(
            first_visit__gte=time_frame.start_date,
            first_visit__lte=time_frame.end_date
        )
        
        return {
            'total_visitors': visitors.count(),
            'new_visitors': visitors.filter(first_visit__gte=time_frame.start_date).count(),
            'returning_visitors': visitors.filter(first_visit__lt=time_frame.start_date).count(),
            'authenticated_visitors': visitors.filter(is_authenticated=True).count(),
            'visitor_locations': visitors.values('country', 'city').annotate(count=Count('id')),
            'device_types': visitors.values('device_type').annotate(count=Count('id')),
            'browsers': visitors.values('browser').annotate(count=Count('id')),
            'operating_systems': visitors.values('os').annotate(count=Count('id'))
        }

    def generate_page_report(self, time_frame):
        """Generate page report data"""
        page_views = PageView.objects.filter(
            timestamp__gte=time_frame.start_date,
            timestamp__lte=time_frame.end_date
        )
        
        return {
            'total_page_views': page_views.count(),
            'unique_pages': page_views.values('path').distinct().count(),
            'average_time_on_page': page_views.aggregate(avg=Avg('duration'))['avg'],
            'bounce_rate': page_views.filter(is_bounce=True).count() / page_views.count() * 100 if page_views.count() > 0 else 0,
            'top_pages': page_views.values('path', 'title').annotate(
                views=Count('id'),
                avg_duration=Avg('duration')
            ).order_by('-views')[:10]
        }

    def generate_conversion_report(self, time_frame):
        """Generate conversion report data"""
        conversions = Conversion.objects.filter(
            timestamp__gte=time_frame.start_date,
            timestamp__lte=time_frame.end_date
        )
        
        return {
            'total_conversions': conversions.count(),
            'conversion_value': conversions.aggregate(total=Sum('value'))['total'],
            'conversion_types': conversions.values('conversion_type').annotate(
                count=Count('id'),
                value=Sum('value')
            ),
            'conversion_rate': conversions.count() / Visitor.objects.filter(
                first_visit__gte=time_frame.start_date,
                first_visit__lte=time_frame.end_date
            ).count() * 100
        }

    def generate_custom_report(self, time_frame, report_config):
        """Generate custom report based on configuration"""
        # Implement custom report generation logic based on report_config
        return {}

class MetricViewSet(viewsets.ModelViewSet):
    """ViewSet for custom metrics"""
    queryset = Metric.objects.all()
    serializer_class = MetricSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Metric.objects.all()
        return Metric.objects.filter(is_active=True)

class AnalyticsSummaryView(generics.RetrieveAPIView):
    """View for overall analytics summary"""
    serializer_class = AnalyticsSummarySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        time_frame = request.query_params.get('time_frame', 'daily')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        if not start_date or not end_date:
            end_date = timezone.now()
            start_date = end_date - timedelta(days=30)

        # Get visitor metrics
        visitor_metrics = Visitor.objects.filter(
            first_visit__gte=start_date,
            first_visit__lte=end_date
        ).aggregate(
            total_visitors=Count('id'),
            new_visitors=Count('id', filter=Q(first_visit__gte=start_date)),
            returning_visitors=Count('id', filter=Q(first_visit__lt=start_date))
        )

        # Get page view metrics
        page_metrics = PageView.objects.filter(
            timestamp__gte=start_date,
            timestamp__lte=end_date
        ).aggregate(
            total_views=Count('id'),
            avg_duration=Avg('duration'),
            bounce_rate=Count('id', filter=Q(is_bounce=True)) * 100.0 / Count('id')
        )

        # Get conversion metrics
        conversion_metrics = Conversion.objects.filter(
            timestamp__gte=start_date,
            timestamp__lte=end_date
        ).aggregate(
            total_conversions=Count('id'),
            conversion_value=Sum('value')
        )

        # Combine all metrics
        summary = {
            'time_frame': time_frame,
            'start_date': start_date,
            'end_date': end_date,
            'visitor_metrics': visitor_metrics,
            'page_metrics': page_metrics,
            'conversion_metrics': conversion_metrics
        }

        serializer = self.get_serializer(summary)
        return Response(serializer.data) 