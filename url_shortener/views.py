"""
Views for URL Shortener API.
Handles creating, redirecting, and managing short URLs.
"""
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponse
from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from datetime import timedelta

from .models import ShortURL, ClickAnalytics
from .serializers import (
    ShortURLCreateSerializer,
    ShortURLResponseSerializer,
    ShortURLStatsSerializer,
)


def get_client_ip(request):
    """Extract client IP from request headers"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_client_country(ip_address):
    """
    Get country from IP address using GeoIP2 (optional).
    Returns empty string if GeoIP2 not configured.
    """
    try:
        from django.contrib.gis.geoip2 import GeoIP2
        g = GeoIP2()
        country = g.country_code(ip_address)
        return country or ''
    except:
        return ''


@api_view(['POST'])
@permission_classes([AllowAny])  # Public API for standalone service
def create_short_url(request):
    """
    Create a new short URL.
    
    POST /api/shorten/
    Body: {
        "original_url": "https://checkout.stripe.com/pay/cs_test_...",
        "domain": "pay.onsync-test.xyz",  // Optional, auto-detected from request
        "title": "Payment Link",  // Optional
        "short_code": "abc123",  // Optional, auto-generated if not provided
        "expires_at": "2024-12-31T23:59:59Z"  // Optional
    }
    
    Returns: {
        "id": 1,
        "short_code": "abc123",
        "original_url": "https://checkout.stripe.com/...",
        "domain": "pay.onsync-test.xyz",
        "full_short_url": "https://pay.onsync-test.xyz/abc123",
        "clicks": 0,
        "created_at": "2024-01-15T10:30:00Z"
    }
    """
    serializer = ShortURLCreateSerializer(
        data=request.data,
        context={'request': request}
    )
    
    if serializer.is_valid():
        short_url = serializer.save()
        response_serializer = ShortURLResponseSerializer(short_url)
        return Response({
            'status': 'success',
            'data': response_serializer.data
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([AllowAny])  # Public endpoint - no authentication required
def redirect_short_url(request, short_code):
    """
    Redirect from short URL to original URL.
    Logs analytics data.
    
    GET /{short_code}/
    
    This is a PUBLIC endpoint (no authentication required).
    Domain is extracted from request.get_host().
    """
    # Get domain from request
    domain = request.get_host()
    
    # Find the short URL
    short_url = get_object_or_404(
        ShortURL,
        short_code=short_code,
        domain=domain,
        is_active=True
    )
    
    # Check if expired
    if short_url.is_expired():
        return HttpResponse(
            '<h1>Link Expired</h1><p>This link has expired and is no longer valid.</p>',
            status=410
        )
    
    # Increment clicks (atomic operation)
    short_url.increment_clicks()
    
    # Log analytics
    ip_address = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    referer = request.META.get('HTTP_REFERER', '')
    country = get_client_country(ip_address)
    
    ClickAnalytics.objects.create(
        short_url=short_url,
        ip_address=ip_address,
        user_agent=user_agent,
        referer=referer,
        country=country,
    )
    
    # Redirect to original URL
    return redirect(short_url.original_url)


@api_view(['GET'])
@permission_classes([AllowAny])  # Public API for standalone service
def get_short_url_stats(request, short_code):
    """
    Get statistics for a short URL.
    
    GET /api/stats/{short_code}/
    
    Returns: {
        "short_url": { ... },
        "total_clicks": 150,
        "recent_clicks": [ ... ],  // Last 100 clicks
        "clicks_by_day": {
            "2024-01-15": 45,
            "2024-01-16": 62,
            ...
        },
        "clicks_by_country": {
            "US": 89,
            "CA": 31,
            "UK": 30
        }
    }
    """
    # Find short URL belonging to this client
    # For now, we'll find by short_code and domain from request
    domain = request.get_host()
    short_url = get_object_or_404(
        ShortURL,
        short_code=short_code,
        domain=domain
    )
    
    # Get analytics data
    analytics = ClickAnalytics.objects.filter(short_url=short_url)
    
    # Total clicks
    total_clicks = short_url.clicks
    
    # Recent clicks (last 100)
    recent_clicks = analytics.order_by('-clicked_at')[:100]
    
    # Clicks by day (last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    clicks_by_day = {}
    daily_clicks = analytics.filter(clicked_at__gte=thirty_days_ago).extra(
        select={'day': 'DATE(clicked_at)'}
    ).values('day').annotate(count=Count('id')).order_by('day')
    
    for item in daily_clicks:
        clicks_by_day[str(item['day'])] = item['count']
    
    # Clicks by country
    clicks_by_country = {}
    country_clicks = analytics.exclude(country='').values('country').annotate(
        count=Count('id')
    ).order_by('-count')
    
    for item in country_clicks:
        clicks_by_country[item['country']] = item['count']
    
    # Build response
    data = {
        'short_url': ShortURLResponseSerializer(short_url).data,
        'total_clicks': total_clicks,
        'recent_clicks': [
            {
                'clicked_at': click.clicked_at,
                'country': click.country,
                'referer': click.referer,
            }
            for click in recent_clicks
        ],
        'clicks_by_day': clicks_by_day,
        'clicks_by_country': clicks_by_country,
    }
    
    return Response(data)


@api_view(['GET'])
@permission_classes([AllowAny])  # Public API for standalone service
def list_short_urls(request):
    """
    List all short URLs for the authenticated account.
    
    GET /api/urls/
    Query params:
    - limit: Number of results (default 50)
    - offset: Pagination offset (default 0)
    - search: Search in title or original_url
    - is_active: Filter by active status (true/false)
    
    Returns: {
        "count": 150,
        "results": [ ... ]
    }
    """
    # Get query params
    limit = int(request.GET.get('limit', 50))
    offset = int(request.GET.get('offset', 0))
    search = request.GET.get('search', '')
    is_active = request.GET.get('is_active', '')
    
    # Build query - filter by domain from request
    domain = request.get_host()
    queryset = ShortURL.objects.filter(domain=domain)
    
    if search:
        queryset = queryset.filter(
            Q(title__icontains=search) | Q(original_url__icontains=search)
        )
    
    if is_active:
        queryset = queryset.filter(is_active=(is_active.lower() == 'true'))
    
    # Get total count
    total_count = queryset.count()
    
    # Apply pagination
    results = queryset[offset:offset + limit]
    
    # Serialize
    serializer = ShortURLResponseSerializer(results, many=True)
    
    return Response({
        'count': total_count,
        'results': serializer.data
    })


@api_view(['DELETE'])
@permission_classes([AllowAny])  # Made public for standalone service
def delete_short_url(request, short_code):
    """
    Delete (deactivate) a short URL.
    
    DELETE /api/urls/{short_code}/
    
    Returns 204 No Content on success.
    """
    domain = request.get_host()
    short_url = get_object_or_404(
        ShortURL,
        short_code=short_code,
        domain=domain
    )
    
    # Soft delete - just deactivate
    short_url.is_active = False
    short_url.save()
    
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['PATCH'])
@permission_classes([AllowAny])  # Made public for standalone service
def update_short_url(request, short_code):
    """
    Update a short URL.
    
    PATCH /api/urls/{short_code}/
    Body: {
        "title": "New Title",
        "is_active": false,
        "expires_at": "2024-12-31T23:59:59Z"
    }
    """
    domain = request.get_host()
    short_url = get_object_or_404(
        ShortURL,
        short_code=short_code,
        domain=domain
    )
    
    # Only allow updating certain fields
    allowed_fields = ['title', 'is_active', 'expires_at']
    for field in allowed_fields:
        if field in request.data:
            setattr(short_url, field, request.data[field])
    
    short_url.save()
    
    serializer = ShortURLResponseSerializer(short_url)
    return Response(serializer.data)
