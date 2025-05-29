from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SiteViewSet, SiteSettingsViewSet

router = DefaultRouter()
router.register(r'sites', SiteViewSet, basename='site')
router.register(r'settings', SiteSettingsViewSet, basename='site-settings')

urlpatterns = [
    path('', include(router.urls)),
]