"""
URL configuration for URL Shortener project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


def health_check(request):
    """Simple health check endpoint"""
    return JsonResponse({'status': 'ok', 'service': 'url-shortener'})


@csrf_exempt
def caddy_validate_domain(request):
    """
    Caddy calls this endpoint to validate domains before issuing SSL certificates.
    Returns 200 to allow certificate issuance, 403 to deny.
    
    This enables on-demand TLS: Caddy will automatically obtain SSL certificates
    for domains that are registered in DomainConfiguration model.
    
    Caddy sends requests like: GET /caddy/validate-domain?domain=forms.example.com
    """
    domain = request.GET.get('domain', '').lower()
    
    if not domain:
        return JsonResponse({'error': 'domain parameter required'}, status=400)
    
    # Check if domain is configured and active in database
    from url_shortener.models import DomainConfiguration
    
    try:
        config = DomainConfiguration.objects.get(
            domain=domain,
            is_active=True
        )
        
        # Domain is configured and active - allow certificate issuance
        return JsonResponse({
            'allow': True,
            'domain': domain,
            'account_id': config.account_id
        })
    
    except DomainConfiguration.DoesNotExist:
        # Domain not configured - deny certificate issuance
        return JsonResponse({
            'allow': False,
            'domain': domain,
            'error': 'Domain not configured'
        }, status=403)


def api_info(request):
    """API information endpoint"""
    return JsonResponse({
        'service': 'URL Shortener',
        'version': '1.0.0',
        'endpoints': {
            'create_short_url': '/api/shorten/',
            'list_urls': '/api/urls/',
            'get_stats': '/api/stats/{short_code}/',
            'redirect': '/{short_code}/',
        },
        'docs': '/api/docs/' if settings.DEBUG else None
    })


urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Health check
    path('health/', health_check, name='health_check'),
    
    # Caddy domain validation (for automatic SSL certificates)
    path('caddy/validate-domain', caddy_validate_domain, name='caddy_validate_domain'),
    
    # API info
    path('api/', api_info, name='api_info'),
    
    # URL shortener app
    path('', include('url_shortener.urls')),
]

# Add API documentation in debug mode
if settings.DEBUG:
    from drf_spectacular.views import (
        SpectacularAPIView,
        SpectacularRedocView,
        SpectacularSwaggerView,
    )
    urlpatterns += [
        path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
        path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
        path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    ]
