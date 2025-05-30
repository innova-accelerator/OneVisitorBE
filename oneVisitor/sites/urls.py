from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router and register viewsets
router = DefaultRouter()
router.register(r'', views.SiteViewSet, basename='site')  # This makes the base path /api/sites/
router.register(r'visitors', views.VisitorViewSet, basename='visitor')
router.register(r'visitor-photos', views.VisitorPhotoViewSet, basename='visitor-photo')

urlpatterns = [
    # ViewSet routes (CRUD operations)
    path('', include(router.urls)),
    
    # Additional utility endpoints
    path('stats/', views.SiteStatsAPIView.as_view(), name='site-stats'),
    path('visitors/stats/', views.VisitorStatsAPIView.as_view(), name='visitor-stats'),
]