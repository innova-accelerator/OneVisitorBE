from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings
from rest_framework import viewsets, status, generics, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.exceptions import TokenError
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.crypto import get_random_string
import json

from .models import UserProfile, JWTToken, UserActivity, EmailVerification, PasswordReset
from .serializers import (
    UserSerializer,
    UserProfileSerializer,
    UserRegistrationSerializer,
    PasswordChangeSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    EmailVerificationSerializer,
)

User = get_user_model()

class UserRegistrationView(generics.CreateAPIView):
    """View for user registration"""
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        user = serializer.save()
        # Create user profile
        UserProfile.objects.create(user=user)
        # Create email verification
        token = get_random_string(64)
        EmailVerification.objects.create(
            user=user,
            token=token,
            expires_at=timezone.now() + timezone.timedelta(days=1)
        )
        # Send verification email
        self.send_verification_email(user, token)

    def send_verification_email(self, user, token):
        subject = 'Verify your email'
        verification_url = f"{settings.FRONTEND_URL}/verify-email/{token}"
        message = render_to_string('users/email/verification_email.html', {
            'user': user,
            'verification_url': verification_url
        })
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=message
        )

class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom token obtain view with activity tracking"""
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            user = User.objects.get(email=request.data['email'])
            # Create JWT token record
            JWTToken.objects.create(
                user=user,
                token=response.data['access'],
                refresh_token=response.data['refresh'],
                expires_at=timezone.now() + timezone.timedelta(minutes=settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].minutes),
                device_info=request.data.get('device_info'),
                ip_address=self.get_client_ip(request)
            )
            # Record activity
            UserActivity.objects.create(
                user=user,
                activity_type='login',
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT')
            )
        return response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class UserViewSet(viewsets.ModelViewSet):
    """ViewSet for user management"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)

    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def logout(self, request):
        try:
            refresh_token = request.data.get('refresh_token')
            token = RefreshToken(refresh_token)
            token.blacklist()
            # Record activity
            UserActivity.objects.create(
                user=request.user,
                activity_type='logout',
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT')
            )
            return Response(status=status.HTTP_204_NO_CONTENT)
        except TokenError:
            return Response(status=status.HTTP_400_BAD_REQUEST)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class UserProfileViewSet(viewsets.ModelViewSet):
    """ViewSet for user profile management"""
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserProfile.objects.filter(user=self.request.user)

    def perform_update(self, serializer):
        instance = serializer.save()
        # Record activity
        UserActivity.objects.create(
            user=self.request.user,
            activity_type='profile_update',
            ip_address=self.get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT'),
            metadata={'updated_fields': list(serializer.validated_data.keys())}
        )
        return instance

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class PasswordChangeView(generics.UpdateAPIView):
    """View for password change"""
    serializer_class = PasswordChangeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        # Record activity
        UserActivity.objects.create(
            user=user,
            activity_type='password_change',
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT')
        )
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class PasswordResetRequestView(generics.CreateAPIView):
    """View for password reset request"""
    serializer_class = PasswordResetRequestSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email=email)
            token = get_random_string(64)
            PasswordReset.objects.create(
                user=user,
                token=token,
                expires_at=timezone.now() + timezone.timedelta(hours=1)
            )
            self.send_reset_email(user, token)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except User.DoesNotExist:
            return Response(status=status.HTTP_204_NO_CONTENT)

    def send_reset_email(self, user, token):
        subject = 'Reset your password'
        reset_url = f"{settings.FRONTEND_URL}/reset-password/{token}"
        message = render_to_string('users/email/reset_password_email.html', {
            'user': user,
            'reset_url': reset_url
        })
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=message
        )

class PasswordResetConfirmView(generics.CreateAPIView):
    """View for password reset confirmation"""
    serializer_class = PasswordResetConfirmSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

class EmailVerificationView(generics.CreateAPIView):
    """View for email verification"""
    serializer_class = EmailVerificationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        verification = serializer.validated_data['verification']
        user = verification.user
        user.is_verified = True
        user.save()
        verification.is_used = True
        verification.save()
        # Record activity
        UserActivity.objects.create(
            user=user,
            activity_type='email_verification',
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT')
        )
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip 