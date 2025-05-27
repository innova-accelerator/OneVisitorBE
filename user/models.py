from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.conf import settings

class UserManager(BaseUserManager):
    """Custom user manager for the User model"""
    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular user with the given email and password"""
        if not email:
            raise ValueError(_('The Email field must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a superuser with the given email and password"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    """Custom user model with email as the primary identifier"""
    username = None
    email = models.EmailField(_('Email address'), unique=True)
    is_verified = models.BooleanField(_('Verified'), default=False)
    created_at = models.DateTimeField(_('Created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated at'), auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        ordering = ['-date_joined']

    def __str__(self):
        return self.email

class UserProfile(models.Model):
    """Extended user profile information"""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name=_('User')
    )
    avatar = models.ImageField(_('Avatar'), upload_to='avatars/', null=True, blank=True)
    phone_number = models.CharField(_('Phone number'), max_length=20, null=True, blank=True)
    company = models.CharField(_('Company'), max_length=100, null=True, blank=True)
    position = models.CharField(_('Position'), max_length=100, null=True, blank=True)
    bio = models.TextField(_('Bio'), null=True, blank=True)
    timezone = models.CharField(_('Timezone'), max_length=50, default='UTC')
    language = models.CharField(_('Language'), max_length=10, default='en')
    notification_preferences = models.JSONField(_('Notification preferences'), default=dict)

    class Meta:
        verbose_name = _('User Profile')
        verbose_name_plural = _('User Profiles')

    def __str__(self):
        return f"{self.user.email}'s profile"

class JWTToken(models.Model):
    """Model to store JWT tokens for user sessions"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='tokens',
        verbose_name=_('User')
    )
    token = models.TextField(_('Token'))
    refresh_token = models.TextField(_('Refresh token'))
    created_at = models.DateTimeField(_('Created at'), auto_now_add=True)
    expires_at = models.DateTimeField(_('Expires at'))
    is_active = models.BooleanField(_('Is active'), default=True)
    device_info = models.JSONField(_('Device info'), null=True, blank=True)
    ip_address = models.GenericIPAddressField(_('IP address'), null=True, blank=True)

    class Meta:
        verbose_name = _('JWT Token')
        verbose_name_plural = _('JWT Tokens')
        ordering = ['-created_at']

    def __str__(self):
        return f"Token for {self.user.email}"

    def is_expired(self):
        return timezone.now() > self.expires_at

class UserActivity(models.Model):
    """Model to track user activities"""
    ACTIVITY_TYPES = (
        ('login', _('Login')),
        ('logout', _('Logout')),
        ('password_change', _('Password Change')),
        ('profile_update', _('Profile Update')),
        ('email_verification', _('Email Verification')),
        ('token_refresh', _('Token Refresh')),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='activities',
        verbose_name=_('User')
    )
    activity_type = models.CharField(_('Activity type'), max_length=50, choices=ACTIVITY_TYPES)
    timestamp = models.DateTimeField(_('Timestamp'), auto_now_add=True)
    ip_address = models.GenericIPAddressField(_('IP address'), null=True, blank=True)
    user_agent = models.TextField(_('User agent'), null=True, blank=True)
    metadata = models.JSONField(_('Additional metadata'), null=True, blank=True)

    class Meta:
        verbose_name = _('User Activity')
        verbose_name_plural = _('User Activities')
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user.email} - {self.activity_type}"

class EmailVerification(models.Model):
    """Model to handle email verification process"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='email_verifications',
        verbose_name=_('User')
    )
    token = models.CharField(_('Verification token'), max_length=100, unique=True)
    created_at = models.DateTimeField(_('Created at'), auto_now_add=True)
    expires_at = models.DateTimeField(_('Expires at'))
    is_used = models.BooleanField(_('Is used'), default=False)

    class Meta:
        verbose_name = _('Email Verification')
        verbose_name_plural = _('Email Verifications')
        ordering = ['-created_at']

    def __str__(self):
        return f"Verification for {self.user.email}"

    def is_expired(self):
        return timezone.now() > self.expires_at

class PasswordReset(models.Model):
    """Model to handle password reset process"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='password_resets',
        verbose_name=_('User')
    )
    token = models.CharField(_('Reset token'), max_length=100, unique=True)
    created_at = models.DateTimeField(_('Created at'), auto_now_add=True)
    expires_at = models.DateTimeField(_('Expires at'))
    is_used = models.BooleanField(_('Is used'), default=False)

    class Meta:
        verbose_name = _('Password Reset')
        verbose_name_plural = _('Password Resets')
        ordering = ['-created_at']

    def __str__(self):
        return f"Reset for {self.user.email}"

    def is_expired(self):
        return timezone.now() > self.expires_at 