from rest_framework import serializers
from .models import Site, SiteMember, SiteDomain, SiteSettings

class SiteDomainSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteDomain
        fields = '__all__'

class SiteSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteSettings
        fields = '__all__'

class SiteMemberSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)

    class Meta:
        model = SiteMember
        fields = ['id', 'user', 'user_email', 'user_name', 'role', 'joined_at', 'is_active']
        read_only_fields = ['joined_at']

class SiteSerializer(serializers.ModelSerializer):
    members = SiteMemberSerializer(many=True, read_only=True)
    domains = SiteDomainSerializer(many=True, read_only=True)
    settings = SiteSettingsSerializer(read_only=True)
    owner_email = serializers.EmailField(source='owner.email', read_only=True)

    class Meta:
        model = Site
        fields = [
            'id', 'name', 'domain', 'owner', 'owner_email',
            'created_at', 'updated_at', 'is_active', 'tracking_code',
            'settings', 'members', 'domains'
        ]
        read_only_fields = ['created_at', 'updated_at', 'tracking_code']