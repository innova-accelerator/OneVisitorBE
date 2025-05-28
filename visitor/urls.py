from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    VisitorViewSet,
    VisitViewSet,
    PageViewViewSet,
    TrackVisitorView,
    TrackPageViewView,
    TrackEventView,
    VisitorStatsView,
    VisitStatsView
)

router = DefaultRouter()
router.register('visitors', VisitorViewSet)
router.register('visits', VisitViewSet)
router.register('pages', PageViewViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('track', TrackVisitorView.as_view()),
    path('track/pageview', TrackPageViewView.as_view()),
    path('track/event', TrackEventView.as_view()),
    path('visitors/stats', VisitorStatsView.as_view()),
    path('visits/stats', VisitStatsView.as_view()),
] 