from rest_framework import serializers
from .models import Site, Visitor, visitorPhoto


class VisitorPhotoSerializer(serializers.ModelSerializer):
    """Serializer for visitor photos"""
    
    class Meta:
        model = visitorPhoto
        fields = ['id', 'file']
        read_only_fields = ['id']


class VisitorListSerializer(serializers.ModelSerializer):
    """Simplified serializer for visitor list views"""
    
    class Meta:
        model = Visitor
        fields = [
            'id', 'name', 'email', 'company', 'phone', 
            'visitorType', 'host', 'purpose'
        ]
        read_only_fields = ['id']


class VisitorDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for visitor with photos"""
    visitorPhoto = VisitorPhotoSerializer(many=True, read_only=True)
    site_name = serializers.CharField(source='site.name', read_only=True)
    
    class Meta:
        model = Visitor
        fields = [
            'id', 'company', 'email', 'expectedDuration', 'host', 
            'name', 'phone', 'purpose', 'signature', 'visitorType',
            'site', 'site_name', 'visitorPhoto'
        ]
        read_only_fields = ['id', 'site_name']


class VisitorCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating visitors"""
    
    class Meta:
        model = Visitor
        fields = [
            'company', 'email', 'expectedDuration', 'host', 
            'name', 'phone', 'purpose', 'signature', 'visitorType', 'site'
        ]
    
    def validate_email(self, value):
        """Validate email format"""
        if value and '@' not in value:
            raise serializers.ValidationError("Enter a valid email address.")
        return value
    
    def validate_phone(self, value):
        """Basic phone validation"""
        if value and not value.replace('+', '').replace('-', '').replace(' ', '').isdigit():
            raise serializers.ValidationError("Enter a valid phone number.")
        return value


class SiteListSerializer(serializers.ModelSerializer):
    """Simplified serializer for site list views"""
    visitor_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Site
        fields = [
            'id', 'name', 'url', 'published', 'language', 
            'lastPublished', 'visitor_count'
        ]
        read_only_fields = ['id', 'visitor_count']
    
    def get_visitor_count(self, obj):
        """Get total number of visitors for this site"""
        return obj.visitor.count()


class SiteDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for site with visitors"""
    visitors = VisitorListSerializer(source='visitor', many=True, read_only=True)
    visitor_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Site
        fields = [
            'id', 'name', 'tenantId', 'url', 'urlType', 'published',
            'logo', 'favicon', 'primaryColor', 'secondaryColor',
            'welcomeMessage', 'language', 'lastPublished', 
            'visitorTypes', 'formFields', 'visitors', 'visitor_count'
        ]
        read_only_fields = ['id', 'visitor_count']
    
    def get_visitor_count(self, obj):
        """Get total number of visitors for this site"""
        return obj.visitor.count()


class SiteCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating sites"""
    
    class Meta:
        model = Site
        fields = [
            'name', 'tenantId', 'url', 'urlType', 'published',
            'logo', 'favicon', 'primaryColor', 'secondaryColor',
            'welcomeMessage', 'language', 'lastPublished', 
            'visitorTypes', 'formFields'
        ]
    
    def validate_url(self, value):
        """Validate URL format"""
        if value and not (value.startswith('http://') or value.startswith('https://')):
            raise serializers.ValidationError("URL must start with http:// or https://")
        return value
    
    def validate_primaryColor(self, value):
        """Validate hex color format"""
        if value and not value.startswith('#'):
            raise serializers.ValidationError("Color must be in hex format (e.g., #FF0000)")
        return value
    
    def validate_secondaryColor(self, value):
        """Validate hex color format"""
        if value and not value.startswith('#'):
            raise serializers.ValidationError("Color must be in hex format (e.g., #FF0000)")
        return value


# Nested serializers for complex operations
class SiteWithVisitorsSerializer(serializers.ModelSerializer):
    """Site serializer with nested visitor details"""
    visitors = VisitorDetailSerializer(source='visitor', many=True, read_only=True)
    
    class Meta:
        model = Site
        fields = '__all__'


class VisitorWithPhotosCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating visitor with photos"""
    photos = VisitorPhotoSerializer(many=True, read_only=True)
    
    class Meta:
        model = Visitor
        fields = [
            'id', 'company', 'email', 'expectedDuration', 'host', 
            'name', 'phone', 'purpose', 'signature', 'visitorType',
            'site', 'photos'
        ]
        read_only_fields = ['id', 'photos']
    
    def create(self, validated_data):
        """Create visitor and handle photo uploads separately"""
        return Visitor.objects.create(**validated_data)