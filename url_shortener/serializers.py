"""
Serializers for URL Shortener API.
"""
from rest_framework import serializers
from .models import ShortURL, ClickAnalytics, DomainConfiguration


class ShortURLCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating short URLs.
    Public API - no client/account required.
    
    Domain handling:
    - If domain is provided, it will be used
    - If not provided, uses request domain from middleware
    - Falls back to localhost for testing
    """
    
    class Meta:
        model = ShortURL
        fields = ['original_url', 'title', 'expires_at', 'domain', 'short_code']
        extra_kwargs = {
            'title': {'required': False, 'allow_blank': True},
            'expires_at': {'required': False, 'allow_null': True},
            'domain': {'required': False, 'allow_blank': True, 'allow_null': True},
            'short_code': {'required': False, 'allow_blank': True, 'allow_null': True},
        }
    
    def validate_original_url(self, value):
        """Basic URL validation"""
        if not value.startswith(('http://', 'https://')):
            raise serializers.ValidationError("URL must start with http:// or https://")
        return value
    
    def create(self, validated_data):
        """Create short URL with domain from request"""
        from django.conf import settings
        
        request = self.context.get('request')
        
        # Determine domain to use
        # IMPORTANT: Only set domain if not explicitly provided
        if not validated_data.get('domain'):
            # Domain not provided, detect from request
            if request and hasattr(request, 'original_host'):
                validated_data['domain'] = request.original_host
            elif request:
                validated_data['domain'] = request.get_host().split(':')[0]
            else:
                validated_data['domain'] = 'localhost'
        
        # Remove None/empty values for optional fields
        if 'short_code' in validated_data and not validated_data.get('short_code'):
            validated_data.pop('short_code')
        
        return super().create(validated_data)


class ShortURLResponseSerializer(serializers.ModelSerializer):
    """
    Serializer for short URL responses.
    Returns all relevant data including the full short URL.
    """
    full_short_url = serializers.ReadOnlyField()
    is_expired = serializers.SerializerMethodField()
    
    class Meta:
        model = ShortURL
        fields = [
            'id',
            'short_code',
            'original_url',
            'domain',
            'full_short_url',
            'title',
            'clicks',
            'is_active',
            'is_expired',
            'created_at',
            'updated_at',
            'expires_at',
        ]
        read_only_fields = ['id', 'short_code', 'clicks', 'created_at', 'updated_at']
    
    def get_is_expired(self, obj):
        """Check if URL is expired"""
        try:
            return obj.is_expired()
        except (TypeError, ValueError) as e:
            # Handle malformed expires_at data
            return False


class ClickAnalyticsSerializer(serializers.ModelSerializer):
    """
    Serializer for click analytics data.
    """
    class Meta:
        model = ClickAnalytics
        fields = [
            'id',
            'clicked_at',
            'ip_address',
            'user_agent',
            'referer',
            'country',
            'city',
        ]


class ShortURLStatsSerializer(serializers.Serializer):
    """
    Serializer for aggregated statistics on a short URL.
    """
    short_url = ShortURLResponseSerializer()
    total_clicks = serializers.IntegerField()
    recent_clicks = serializers.ListField(
        child=ClickAnalyticsSerializer()
    )
    clicks_by_day = serializers.DictField()
    clicks_by_country = serializers.DictField()


class BulkShortURLSerializer(serializers.Serializer):
    """
    Serializer for bulk URL shortening operations.
    """
    urls = serializers.ListField(
        child=serializers.URLField(),
        min_length=1,
        max_length=100
    )
    domain = serializers.CharField(required=False)


# =============================================================================
# Internal API Serializers (for domain configuration)
# =============================================================================

class DomainConfigurationSerializer(serializers.ModelSerializer):
    """
    Serializer for domain configuration.
    Used by internal API for domain management.
    """
    class Meta:
        model = DomainConfiguration
        fields = [
            'id',
            'domain',
            'account_id',
            'domain_type',
            'is_verified',
            'is_active',
            'ssl_status',
            'configured_at',
            'updated_at',
            'ssl_issued_at',
            'ssl_expires_at',
            'use_caddy',
            'notes',
        ]
        read_only_fields = [
            'id',
            'configured_at',
            'updated_at',
            'ssl_issued_at',
            'ssl_expires_at',
        ]
    
    def validate_domain(self, value):
        """Validate domain format."""
        import re
        # Basic domain validation
        domain_pattern = r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
        if not re.match(domain_pattern, value):
            raise serializers.ValidationError("Invalid domain format")
        return value.lower()


class DomainConfigureRequestSerializer(serializers.Serializer):
    """
    Serializer for domain configuration requests from CRM backend.
    """
    domain = serializers.CharField(max_length=255)
    account_id = serializers.IntegerField()
    domain_type = serializers.ChoiceField(
        choices=['forms', 'payment', 'other'],
        default='forms'
    )
    use_caddy = serializers.BooleanField(default=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate_domain(self, value):
        """Validate domain format."""
        import re
        domain_pattern = r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
        if not re.match(domain_pattern, value):
            raise serializers.ValidationError("Invalid domain format")
        return value.lower()


class DomainStatusSerializer(serializers.ModelSerializer):
    """
    Serializer for domain status responses.
    """
    class Meta:
        model = DomainConfiguration
        fields = [
            'domain',
            'is_verified',
            'is_active',
            'ssl_status',
            'ssl_issued_at',
            'ssl_expires_at',
            'configured_at',
        ]
