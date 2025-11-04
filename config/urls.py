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
