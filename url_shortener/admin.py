"""
Django admin interface for URL Shortener.
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import ShortURL, ClickAnalytics, DomainConfiguration


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


@admin.register(DomainConfiguration)
class DomainConfigurationAdmin(admin.ModelAdmin):
    """Admin interface for managing domain configurations"""
    
    list_display = [
        'domain',
        'account_id',
        'domain_type',
        'ssl_status_badge',
        'is_verified',
        'is_active',
        'configured_at',
    ]
    
    list_filter = [
        'domain_type',
        'ssl_status',
        'is_verified',
        'is_active',
        'use_caddy',
        'configured_at',
    ]
    
    search_fields = [
        'domain',
        'account_id',
        'notes',
    ]
    
    readonly_fields = [
        'configured_at',
        'updated_at',
        'ssl_issued_at',
    ]
    
    fieldsets = (
        ('Domain Information', {
            'fields': ('domain', 'account_id', 'domain_type')
        }),
        ('Status', {
            'fields': ('is_active', 'is_verified', 'ssl_status')
        }),
        ('SSL Certificate', {
            'fields': ('use_caddy', 'ssl_issued_at', 'ssl_expires_at'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('configured_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    date_hierarchy = 'configured_at'
    
    def ssl_status_badge(self, obj):
        """Display SSL status with color badge"""
        colors = {
            'pending': 'orange',
            'active': 'green',
            'failed': 'red',
            'expired': 'gray',
        }
        color = colors.get(obj.ssl_status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">● {}</span>',
            color,
            obj.ssl_status.upper()
        )
    ssl_status_badge.short_description = 'SSL Status'
    
    actions = ['mark_as_verified', 'mark_as_active', 'mark_ssl_active']
    
    @admin.action(description='Mark selected domains as verified')
    def mark_as_verified(self, request, queryset):
        updated = queryset.update(is_verified=True)
        self.message_user(request, f'{updated} domain(s) marked as verified.')
    
    @admin.action(description='Mark selected domains as active')
    def mark_as_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} domain(s) marked as active.')
    
    @admin.action(description='Mark SSL as active for selected domains')
    def mark_ssl_active(self, request, queryset):
        for domain in queryset:
            domain.mark_ssl_active()
        self.message_user(request, f'{queryset.count()} domain(s) SSL marked as active.')
