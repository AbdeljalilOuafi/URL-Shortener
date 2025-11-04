"""
Middleware for handling multiple domains in URL shortener.
No client validation - accepts all domains (public service).
"""
from django.conf import settings


class MultiDomainMiddleware:
    """
    Middleware to handle requests from multiple short URL domains.
    Adds domain context to the request for public service.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Get the host from request
        host = request.get_host().split(':')[0]  # Remove port if present
        
        # Add domain to request for easy access
        request.short_url_domain = host
        
        # Store original host for later use
        request.original_host = host
        
        response = self.get_response(request)
        return response
