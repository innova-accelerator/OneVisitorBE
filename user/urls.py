from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet,
    LoginView,
    LogoutView,
    RegisterView,
    RefreshTokenView
)

router = DefaultRouter()
router.register('users', UserViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/login', LoginView.as_view()),
    path('auth/logout', LogoutView.as_view()),
    path('auth/register', RegisterView.as_view()),
    path('auth/refresh', RefreshTokenView.as_view()),
] 