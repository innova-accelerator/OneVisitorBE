from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    VisitorViewSet, SessionViewSet,
    PageViewViewSet, EventViewSet
)

router = DefaultRouter()
router.register(r'visitors', VisitorViewSet)
router.register(r'sessions', SessionViewSet)
router.register(r'page-views', PageViewViewSet)
router.register(r'events', EventViewSet)

urlpatterns = [
    path('', include(router.urls)),
]