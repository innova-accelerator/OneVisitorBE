from rest_framework import serializers
from .models import Site, Host, Visitor, visitorPhoto
import pytz
from dateutil import parser


def get_timezone_abbreviation(offset_minutes):
    """Get timezone abbreviation from offset in minutes"""
    hours = offset_minutes // 60
    minutes = abs(offset_minutes % 60)
    
    if hours >= 0:
        return f"UTC+{hours:02d}:{minutes:02d}"
    else:
        return f"UTC{hours:03d}:{minutes:02d}"


class VisitorPhotoSerializer(serializers.ModelSerializer):
    """Serializer for visitor photos"""
    
    class Meta:
        model = visitorPhoto
        fields = ['id', 'file']
        read_only_fields = ['id']


class HostListSerializer(serializers.ModelSerializer):
    """Simplified serializer for host list views"""
    visitor_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Host
        fields = ['id', 'name', 'email', 'phone', 'department', 'visitor_count']
        read_only_fields = ['id', 'visitor_count']
    
    def get_visitor_count(self, obj):
        """Get total number of visitors for this host"""
        return obj.visitor.count()


class HostDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for host with site info"""
    site_name = serializers.CharField(source='site.name', read_only=True)
    visitor_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Host
        fields = [
            'id', 'name', 'email', 'phone', 'department', 
            'site', 'site_name', 'visitor_count'
        ]
        read_only_fields = ['id', 'site_name', 'visitor_count']
    
    def get_visitor_count(self, obj):
        """Get total number of visitors for this host"""
        return obj.visitor.count()


class HostCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating hosts"""
    
    class Meta:
        model = Host
        fields = ['name', 'email', 'phone', 'department', 'site']
    
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


class VisitorListSerializer(serializers.ModelSerializer):
    """Simplified serializer for visitor list views"""
    host_name = serializers.CharField(source='host.name', read_only=True)
    site_name = serializers.CharField(source='site.name', read_only=True)
    
    class Meta:
        model = Visitor
        fields = [
            'id', 'name', 'email', 'company', 'phone', 
            'visitorType', 'host', 'host_name', 'site_name', 'purpose'
        ]
        read_only_fields = ['id', 'host_name', 'site_name']


class VisitorDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for visitor with photos and related info"""
    visitorPhoto = VisitorPhotoSerializer(many=True, read_only=True)
    host_details = HostListSerializer(source='host', read_only=True)
    site_name = serializers.CharField(source='site.name', read_only=True)
    
    class Meta:
        model = Visitor
        fields = [
            'id', 'company', 'email', 'expectedDuration', 'host', 'host_details',
            'name', 'phone', 'purpose', 'signature', 'visitorType',
            'site', 'site_name', 'visitorPhoto'
        ]
        read_only_fields = ['id', 'host_details', 'site_name']


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
    
    def validate(self, data):
        """Validate that host belongs to the same site"""
        if 'host' in data and 'site' in data:
            if data['host'].site != data['site']:
                raise serializers.ValidationError(
                    "Selected host does not belong to the specified site."
                )
        return data


class SiteListSerializer(serializers.ModelSerializer):
    """Simplified serializer for site list views"""
    visitor_count = serializers.SerializerMethodField()
    host_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Site
        fields = [
            'id', 'name', 'url', 'published', 'language', 
            'lastPublished', 'visitor_count', 'host_count'
        ]
        read_only_fields = ['id', 'visitor_count', 'host_count']
    
    def get_visitor_count(self, obj):
        """Get total number of visitors for this site"""
        return obj.visitor.count()
    
    def get_host_count(self, obj):
        """Get total number of hosts for this site"""
        return obj.host.count()


class SiteDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for site with hosts and visitors"""
    hosts = HostListSerializer(source='host', many=True, read_only=True)
    recent_visitors = serializers.SerializerMethodField()
    visitor_count = serializers.SerializerMethodField()
    host_count = serializers.SerializerMethodField()
    lastPublished = serializers.SerializerMethodField()
    
    class Meta:
        model = Site
        fields = [
            'id', 'name', 'tenantId', 'url', 'urlType', 'published',
            'logo', 'favicon', 'primaryColor', 'secondaryColor',
            'welcomeMessage', 'language', 'lastPublished', 'timezoneOffset',
            'visitorTypes', 'formFields', 'hosts', 'recent_visitors',
            'visitor_count', 'host_count'
        ]
        read_only_fields = ['id', 'visitor_count', 'host_count', 'recent_visitors']
    
    def get_lastPublished(self, obj):
        """Get lastPublished with timezone conversion"""
        if not obj.lastPublished:
            return None
            
        timeoffsetOri = obj.timezoneOffset
        if timeoffsetOri and timeoffsetOri != "UTC":
            try:
                target_tz = pytz.FixedOffset(-int(timeoffsetOri))  # Notice the negative sign here
                
                # Convert the datetime
                dt = obj.lastPublished
                if isinstance(dt, str):
                    dt = parser.parse(dt)
                
                # For DateField, we need to convert to datetime first
                if hasattr(dt, 'date') and not hasattr(dt, 'hour'):
                    # This is a date object, convert to datetime at midnight UTC
                    from datetime import datetime, time
                    dt = datetime.combine(dt, time.min)
                
                # Ensure dt has timezone info
                if dt.tzinfo is None:
                    dt = pytz.UTC.localize(dt)
                    
                # Convert to target timezone
                local_dt = dt.astimezone(target_tz)
                abb = get_timezone_abbreviation(-int(timeoffsetOri))
                return local_dt.strftime('%m/%d/%Y %I:%M %p') + " " + abb
            except (ValueError, TypeError):
                # Fallback to original format if conversion fails
                return obj.lastPublished.strftime('%m/%d/%Y') if obj.lastPublished else None
        else:
            return obj.lastPublished.strftime('%m/%d/%Y') if obj.lastPublished else None
    
    def get_visitor_count(self, obj):
        """Get total number of visitors for this site"""
        return obj.visitor.count()
    
    def get_host_count(self, obj):
        """Get total number of hosts for this site"""
        return obj.host.count()
    
    def get_recent_visitors(self, obj):
        """Get last 5 visitors for this site"""
        recent_visitors = obj.visitor.all().order_by('-id')[:5]
        return VisitorListSerializer(recent_visitors, many=True).data


class SiteCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating sites"""
    
    class Meta:
        model = Site
        fields = [
            'name', 'tenantId', 'url', 'urlType', 'published',
            'logo', 'favicon', 'primaryColor', 'secondaryColor',
            'welcomeMessage', 'language', 'timezoneOffset',
            'visitorTypes', 'formFields'
        ]
        # Remove lastPublished from fields - it will be auto-managed
    
    def validate_url(self, value):
        """Validate URL format"""
        if value and not (value.startswith('http://') or value.startswith('https://') or value.startswith('/')):
            # Allow relative paths or full URLs
            return value
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
    
    def to_internal_value(self, data):
        """Handle nested branding object if present"""
        # Make a copy to avoid modifying the original data
        data_copy = data.copy()
        
        # If branding is nested, flatten it
        if 'branding' in data_copy:
            branding = data_copy.pop('branding')
            data_copy.update({
                'logo': branding.get('logo', ''),
                'primaryColor': branding.get('primaryColor', ''),
                'secondaryColor': branding.get('secondaryColor', ''),
                'favicon': branding.get('favicon', '')
            })
        
        return super().to_internal_value(data_copy)


# Nested serializers for complex operations
class SiteWithHostsAndVisitorsSerializer(serializers.ModelSerializer):
    """Site serializer with nested hosts and visitors"""
    hosts = HostDetailSerializer(source='host', many=True, read_only=True)
    visitors = VisitorDetailSerializer(source='visitor', many=True, read_only=True)
    
    class Meta:
        model = Site
        fields = '__all__'


class HostWithVisitorsSerializer(serializers.ModelSerializer):
    """Host serializer with nested visitors"""
    visitors = VisitorListSerializer(source='visitor', many=True, read_only=True)
    site_name = serializers.CharField(source='site.name', read_only=True)
    
    class Meta:
        model = Host
        fields = [
            'id', 'name', 'email', 'phone', 'department', 
            'site', 'site_name', 'visitors'
        ]
        read_only_fields = ['id', 'site_name']


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
    
    def validate(self, data):
        """Validate that host belongs to the same site"""
        if 'host' in data and 'site' in data:
            if data['host'].site != data['site']:
                raise serializers.ValidationError(
                    "Selected host does not belong to the specified site."
                )
        return data
    
    def create(self, validated_data):
        """Create visitor and handle photo uploads separately"""
        return Visitor.objects.create(**validated_data)


# Utility serializers for dropdowns/choices
class HostChoiceSerializer(serializers.ModelSerializer):
    """Simple serializer for host dropdown choices"""
    
    class Meta:
        model = Host
        fields = ['id', 'name', 'department']


class SiteChoiceSerializer(serializers.ModelSerializer):
    """Simple serializer for site dropdown choices"""
    
    class Meta:
        model = Site
        fields = ['id', 'name', 'published']