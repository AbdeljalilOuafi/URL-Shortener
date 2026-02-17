"""
URL routing for URL Shortener.
"""
from django.urls import path
from . import views
from . import internal_views

app_name = 'url_shortener'

urlpatterns = [
    # Public API endpoints
    path('api/shorten/', views.create_short_url, name='create'),
    path('api/urls/', views.list_short_urls, name='list'),
    path('api/urls/<str:short_code>/', views.update_short_url, name='update'),
    path('api/stats/<str:short_code>/', views.get_short_url_stats, name='stats'),
    path('api/urls/<str:short_code>/delete/', views.delete_short_url, name='delete'),
    
    # Internal API endpoints (require X-Internal-API-Key header)
    path('api/internal/domains/configure/', internal_views.configure_domain, name='internal_configure_domain'),
    path('api/internal/domains/<str:domain>/status/', internal_views.get_domain_status, name='internal_domain_status'),
    path('api/internal/domains/<str:domain>/', internal_views.remove_domain, name='internal_remove_domain'),
    path('api/internal/domains/<str:domain>/ssl-status/', internal_views.update_domain_ssl_status, name='internal_update_ssl_status'),
    path('api/internal/accounts/<int:account_id>/domains/', internal_views.list_account_domains, name='internal_list_account_domains'),
    
    # Public redirect endpoint (no auth required)
    # This is a catch-all and should be included LAST in the main urls.py
    path('<str:short_code>/', views.redirect_short_url, name='redirect'),
]
