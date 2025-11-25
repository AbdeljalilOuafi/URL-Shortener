"""
Serializers for URL Shortener API.
"""
from rest_framework import serializers
from .models import ShortURL, ClickAnalytics


class ShortURLCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating short URLs.
    Public API - no client/account required.
    
    Domain handling:
    - If domain is provided, it will be used
    - If not provided, uses request domain from middleware
    - Falls back to localhost for testing
    """
    # Explicitly declare optional fields
    domain = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=255)
    short_code = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=10)
    
    class Meta:
        model = ShortURL
        fields = ['original_url', 'title', 'expires_at', 'domain', 'short_code']
        extra_kwargs = {
            'title': {'required': False},
            'expires_at': {'required': False},
            'domain': {'required': False},
            'short_code': {'required': False},
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
