from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.contrib.auth.password_validation import validate_password
from .models import UserProfile, JWTToken, UserActivity, EmailVerification, PasswordReset

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """Base serializer for User model"""
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'is_active',
            'is_staff', 'date_joined', 'last_login'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login']

class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password2 = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = [
            'email', 'password', 'password2', 'first_name', 'last_name'
        ]

    def validate(self, data):
        """Validate that passwords match"""
        if data['password'] != data['password2']:
            raise serializers.ValidationError(
                _("Passwords don't match")
            )
        return data

    def create(self, validated_data):
        """Create new user"""
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user

class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user information"""
    class Meta:
        model = User
        fields = ['first_name', 'last_name']

class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile"""
    user = UserSerializer(read_only=True)
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = [
            'id', 'user', 'full_name', 'phone_number', 'company',
            'position', 'bio', 'avatar', 'preferences', 'created_at',
            'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_full_name(self, obj):
        """Get user's full name"""
        return f"{obj.user.first_name} {obj.user.last_name}".strip()

class JWTTokenSerializer(serializers.ModelSerializer):
    """Serializer for JWT tokens"""
    class Meta:
        model = JWTToken
        fields = [
            'id', 'user', 'token', 'refresh_token', 'expires_at',
            'is_revoked', 'created_at'
        ]
        read_only_fields = ['id', 'token', 'refresh_token', 'expires_at', 'created_at']

class UserActivitySerializer(serializers.ModelSerializer):
    """Serializer for user activity"""
    user = UserSerializer(read_only=True)

    class Meta:
        model = UserActivity
        fields = [
            'id', 'user', 'activity_type', 'ip_address', 'user_agent',
            'details', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class EmailVerificationSerializer(serializers.ModelSerializer):
    """Serializer for email verification"""
    class Meta:
        model = EmailVerification
        fields = [
            'id', 'user', 'token', 'is_verified', 'expires_at',
            'created_at'
        ]
        read_only_fields = ['id', 'token', 'expires_at', 'created_at']

class PasswordResetSerializer(serializers.ModelSerializer):
    """Serializer for password reset"""
    class Meta:
        model = PasswordReset
        fields = [
            'id', 'user', 'token', 'is_used', 'expires_at',
            'created_at'
        ]
        read_only_fields = ['id', 'token', 'expires_at', 'created_at']

class LoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )

    def validate(self, data):
        """Validate user credentials"""
        user = authenticate(
            request=self.context.get('request'),
            email=data['email'],
            password=data['password']
        )

        if not user:
            raise serializers.ValidationError(
                _("Invalid email or password")
            )

        if not user.is_active:
            raise serializers.ValidationError(
                _("User account is disabled")
            )

        data['user'] = user
        return data

class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing password"""
    old_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    new_password2 = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )

    def validate(self, data):
        """Validate password change"""
        if data['new_password'] != data['new_password2']:
            raise serializers.ValidationError(
                _("New passwords don't match")
            )
        return data

    def validate_old_password(self, value):
        """Validate old password"""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError(
                _("Invalid old password")
            )
        return value

class RequestPasswordResetSerializer(serializers.Serializer):
    """Serializer for requesting password reset"""
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        """Validate email exists"""
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                _("No user found with this email address")
            )
        return value

class VerifyEmailSerializer(serializers.Serializer):
    """Serializer for email verification"""
    token = serializers.CharField(required=True)

    def validate_token(self, value):
        """Validate verification token"""
        try:
            verification = EmailVerification.objects.get(
                token=value,
                is_verified=False,
                expires_at__gt=timezone.now()
            )
        except EmailVerification.DoesNotExist:
            raise serializers.ValidationError(
                _("Invalid or expired verification token")
            )
        return value

class RefreshTokenSerializer(serializers.Serializer):
    """Serializer for refreshing JWT token"""
    refresh_token = serializers.CharField(required=True)

    def validate_refresh_token(self, value):
        """Validate refresh token"""
        try:
            token = JWTToken.objects.get(
                refresh_token=value,
                is_revoked=False,
                expires_at__gt=timezone.now()
            )
        except JWTToken.DoesNotExist:
            raise serializers.ValidationError(
                _("Invalid or expired refresh token")
            )
        return value

class UserPreferencesSerializer(serializers.Serializer):
    """Serializer for user preferences"""
    theme = serializers.ChoiceField(
        choices=['light', 'dark', 'system'],
        default='system'
    )
    language = serializers.ChoiceField(
        choices=['en', 'es', 'fr', 'de'],
        default='en'
    )
    notifications = serializers.DictField(
        child=serializers.BooleanField(),
        default=dict
    )
    timezone = serializers.CharField(default='UTC')
    date_format = serializers.CharField(default='YYYY-MM-DD')
    time_format = serializers.CharField(default='24h')

class UserStatsSerializer(serializers.Serializer):
    """Serializer for user statistics"""
    total_visits = serializers.IntegerField()
    last_visit = serializers.DateTimeField()
    average_session_duration = serializers.DurationField()
    favorite_pages = serializers.ListField(
        child=serializers.DictField()
    )
    conversion_rate = serializers.FloatField()
    engagement_score = serializers.FloatField() 