"""
Django admin interface for URL Shortener.
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import ShortURL, ClickAnalytics


@admin.register(ShortURL)
class ShortURLAdmin(admin.ModelAdmin):
    """Admin interface for managing short URLs"""
    
    list_display = [
        'short_code',
        'domain',
        'title',
        'clicks',
        'is_active',
        'created_at',
        'full_url_link',
    ]
    
    list_filter = [
        'is_active',
        'domain',
        'created_at',
    ]
    
    search_fields = [
        'short_code',
        'title',
        'original_url',
        'domain',
    ]
    
    readonly_fields = [
        'short_code',
        'clicks',
        'created_at',
        'updated_at',
        'full_short_url',
    ]
    
    fieldsets = (
        ('URL Information', {
            'fields': ('short_code', 'original_url', 'full_short_url', 'domain')
        }),
        ('Metadata', {
            'fields': ('title', 'clicks')
        }),
        ('Status', {
            'fields': ('is_active', 'expires_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    date_hierarchy = 'created_at'
    
    def full_url_link(self, obj):
        """Clickable link to the short URL"""
        return format_html(
            '<a href="{}" target="_blank">{}</a>',
            obj.full_short_url,
            obj.full_short_url
        )
    full_url_link.short_description = 'Full Short URL'


@admin.register(ClickAnalytics)
class ClickAnalyticsAdmin(admin.ModelAdmin):
    """Admin interface for viewing click analytics"""
    
    list_display = [
        'short_url_code',
        'clicked_at',
        'country',
        'ip_address',
        'referer_short',
    ]
    
    list_filter = [
        'clicked_at',
        'country',
    ]
    
    search_fields = [
        'short_url__short_code',
        'ip_address',
        'referer',
    ]
    
    readonly_fields = [
        'short_url',
        'clicked_at',
        'ip_address',
        'user_agent',
        'referer',
        'country',
        'city',
    ]
    
    date_hierarchy = 'clicked_at'
    
    def short_url_code(self, obj):
        """Display short code of the URL"""
        return obj.short_url.short_code
    short_url_code.short_description = 'Short Code'
    
    def referer_short(self, obj):
        """Display truncated referer"""
        if obj.referer:
            return obj.referer[:50] + '...' if len(obj.referer) > 50 else obj.referer
        return '-'
    referer_short.short_description = 'Referer'
    
    def has_add_permission(self, request):
        """Disable manual creation of analytics - they're auto-generated"""
        return False
