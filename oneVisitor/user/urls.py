from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from .views import *

urlpatterns = [
    # Authentication endpoints
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('logout/', logout_view, name='logout'),
    
    # User management endpoints
    path('register/', RegisterView.as_view(), name='register'),
    path('profile/', UserDetailView.as_view(), name='user_profile'),
    path('profile/update/', UserDetailView.as_view(), name='user_profile_update'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    
    # Alternative profile endpoint
    path('me/', user_profile, name='current_user'),
]