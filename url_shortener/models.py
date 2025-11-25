"""
Models for URL Shortener with multi-domain support.
No authentication required - public service.
"""
from django.db import models
from django.utils import timezone
import secrets
import string


def generate_short_code(length=6):
    """Generate a random short code using alphanumeric characters"""
    characters = string.ascii_letters + string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))


class ShortURL(models.Model):
    """
    Stores shortened URLs with multi-domain support.
    No client/account relationship - fully public service.
    """
    
    short_code = models.CharField(
        max_length=10,
        db_index=True,
        help_text="Unique short code (e.g., 'abc123')"
    )
    
    original_url = models.URLField(
        max_length=2048,
        help_text="The original long URL to redirect to"
    )
    
    domain = models.CharField(
        max_length=255,
        db_index=True,
        help_text="The domain for this short URL (e.g., 'pay.ao.com')"
    )
    
    title = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Optional title/description for the link"
    )
    
    clicks = models.IntegerField(
        default=0,
        help_text="Number of times this URL has been clicked"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Optional: Expiration
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Optional expiration date for the link"
    )
    
    # Optional: Enable/disable
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this short URL is active"
    )
    
    class Meta:
        db_table = 'short_urls'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['short_code']),
            models.Index(fields=['domain', 'short_code']),
            models.Index(fields=['created_at']),
        ]
        unique_together = [['domain', 'short_code']]
    
    def __str__(self):
        return f"{self.domain}/{self.short_code} → {self.original_url[:50]}"
    
    def save(self, *args, **kwargs):
        """Auto-generate short code if not provided"""
        if not self.short_code:
            # Keep generating until we find a unique code for this domain
            max_attempts = 10
            for _ in range(max_attempts):
                code = generate_short_code()
                if not ShortURL.objects.filter(short_code=code, domain=self.domain).exists():
                    self.short_code = code
                    break
            else:
                # If we couldn't find a unique code, try with longer length
                code = generate_short_code(8)
                self.short_code = code
        
        super().save(*args, **kwargs)
    
    @property
    def full_short_url(self):
        """Returns the complete short URL"""
        return f"https://{self.domain}/{self.short_code}"
    
    def is_expired(self):
        """Check if URL has expired"""
        if self.expires_at:
            # Handle both datetime and string cases
            if isinstance(self.expires_at, str):
                from dateutil import parser
                expires_dt = parser.parse(self.expires_at)
                return timezone.now() > expires_dt
            return timezone.now() > self.expires_at
        return False
    
    def increment_clicks(self):
        """Increment click count atomically (thread-safe)"""
        ShortURL.objects.filter(pk=self.pk).update(clicks=models.F('clicks') + 1)


class ClickAnalytics(models.Model):
    """
    Track detailed click analytics for short URLs.
    Optional but recommended for understanding traffic patterns.
    """
    short_url = models.ForeignKey(
        ShortURL,
        on_delete=models.CASCADE,
        related_name='analytics'
    )
    
    clicked_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    # Request metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    referer = models.URLField(max_length=2048, blank=True)
    
    # Geographic data (can be populated using GeoIP2)
    country = models.CharField(max_length=2, blank=True)
    city = models.CharField(max_length=100, blank=True)
    
    class Meta:
        db_table = 'click_analytics'
        ordering = ['-clicked_at']
        indexes = [
            models.Index(fields=['short_url', 'clicked_at']),
            models.Index(fields=['clicked_at']),
        ]
        verbose_name_plural = 'Click analytics'
    
    def __str__(self):
        return f"Click on {self.short_url.short_code} at {self.clicked_at}"
