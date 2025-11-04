"""
URL routing for URL Shortener.
"""
from django.urls import path
from . import views

app_name = 'url_shortener'

urlpatterns = [
    # API endpoints (authenticated)
    path('api/shorten/', views.create_short_url, name='create'),
    path('api/urls/', views.list_short_urls, name='list'),
    path('api/urls/<str:short_code>/', views.update_short_url, name='update'),
    path('api/stats/<str:short_code>/', views.get_short_url_stats, name='stats'),
    path('api/urls/<str:short_code>/delete/', views.delete_short_url, name='delete'),
    
    # Public redirect endpoint (no auth required)
    # This is a catch-all and should be included LAST in the main urls.py
    path('<str:short_code>/', views.redirect_short_url, name='redirect'),
]
