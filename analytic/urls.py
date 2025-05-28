from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ReportViewSet,
    DashboardViewSet,
    AnalyticsOverviewView,
    RealtimeAnalyticsView,
    ExportAnalyticsView,
    CustomReportView
)

router = DefaultRouter()
router.register('reports', ReportViewSet)
router.register('dashboards', DashboardViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('overview', AnalyticsOverviewView.as_view()),
    path('realtime', RealtimeAnalyticsView.as_view()),
    path('export', ExportAnalyticsView.as_view()),
    path('custom-report', CustomReportView.as_view()),
] 