"""
Internal API Views for URL Shortener

These endpoints are used by the CRM backend to manage domain configurations.
All endpoints require authentication via X-Internal-API-Key header.
"""
import logging
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db import IntegrityError
from functools import wraps

from .models import DomainConfiguration
from .serializers import (
    DomainConfigurationSerializer,
    DomainConfigureRequestSerializer,
    DomainStatusSerializer,
)

logger = logging.getLogger(__name__)


def require_internal_api_key(view_func):
    """
    Decorator to require internal API key authentication.
    Checks X-Internal-API-Key header against settings.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        api_key = request.headers.get('X-Internal-API-Key')
        expected_key = getattr(settings, 'INTERNAL_API_KEY', '')
        
        if not expected_key:
            logger.error("INTERNAL_API_KEY not configured in settings")
            return Response(
                {"error": "Internal API not properly configured"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        if not api_key:
            logger.warning("Internal API request missing X-Internal-API-Key header")
            return Response(
                {"error": "Authentication required"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        if api_key != expected_key:
            logger.warning(f"Invalid internal API key attempted from {request.META.get('REMOTE_ADDR')}")
            return Response(
                {"error": "Invalid authentication credentials"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


@api_view(['POST'])
@require_internal_api_key
def configure_domain(request):
    """
    Configure a new domain for the URL shortener.
    
    POST /api/internal/domains/configure/
    
    Request Body:
    {
        "domain": "forms.clientbusiness.com",
        "account_id": 123,
        "domain_type": "forms",  # optional: forms, payment, other
        "use_caddy": true,       # optional: default true
        "notes": ""              # optional
    }
    
    Response:
    {
        "status": "success",
        "domain": "forms.clientbusiness.com",
        "message": "Domain configured successfully",
        "data": {
            "id": 1,
            "domain": "forms.clientbusiness.com",
            "account_id": 123,
            "is_verified": false,
            "is_active": true,
            "ssl_status": "pending",
            ...
        }
    }
    """
    serializer = DomainConfigureRequestSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(
            {
                "status": "error",
                "errors": serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    data = serializer.validated_data
    domain = data['domain']
    account_id = data['account_id']
    
    try:
        # Check if domain already exists
        existing = DomainConfiguration.objects.filter(domain=domain).first()
        if existing:
            if existing.is_active:
                return Response(
                    {
                        "status": "error",
                        "error": "Domain already configured",
                        "domain": domain
                    },
                    status=status.HTTP_409_CONFLICT
                )
            else:
                # Reactivate inactive domain
                existing.is_active = True
                existing.account_id = account_id
                existing.domain_type = data.get('domain_type', 'forms')
                existing.use_caddy = data.get('use_caddy', True)
                existing.notes = data.get('notes', '')
                existing.ssl_status = 'pending'
                existing.save()
                
                logger.info(f"Reactivated domain {domain} for account {account_id}")
                
                response_serializer = DomainConfigurationSerializer(existing)
                return Response(
                    {
                        "status": "success",
                        "message": "Domain reactivated successfully",
                        "domain": domain,
                        "data": response_serializer.data
                    },
                    status=status.HTTP_200_OK
                )
        
        # Create new domain configuration
        domain_config = DomainConfiguration.objects.create(
            domain=domain,
            account_id=account_id,
            domain_type=data.get('domain_type', 'forms'),
            use_caddy=data.get('use_caddy', True),
            notes=data.get('notes', ''),
            is_active=True,
            is_verified=False,  # Will be verified on first successful request
            ssl_status='pending'
        )
        
        logger.info(f"Configured new domain {domain} for account {account_id}")
        
        response_serializer = DomainConfigurationSerializer(domain_config)
        return Response(
            {
                "status": "success",
                "message": "Domain configured successfully. SSL certificate will be issued on first request.",
                "domain": domain,
                "data": response_serializer.data
            },
            status=status.HTTP_201_CREATED
        )
    
    except IntegrityError as e:
        logger.error(f"Database integrity error configuring domain {domain}: {str(e)}")
        return Response(
            {
                "status": "error",
                "error": "Database error configuring domain"
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        logger.exception(f"Unexpected error configuring domain {domain}: {str(e)}")
        return Response(
            {
                "status": "error",
                "error": "Internal server error"
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@require_internal_api_key
def get_domain_status(request, domain):
    """
    Get the configuration status of a domain.
    
    GET /api/internal/domains/{domain}/status/
    
    Response:
    {
        "status": "success",
        "data": {
            "domain": "forms.clientbusiness.com",
            "is_verified": true,
            "is_active": true,
            "ssl_status": "active",
            "ssl_issued_at": "2026-02-16T10:00:00Z",
            "ssl_expires_at": "2026-05-16T10:00:00Z",
            "configured_at": "2026-02-16T09:00:00Z"
        }
    }
    """
    try:
        domain_config = DomainConfiguration.objects.get(domain=domain.lower())
        serializer = DomainStatusSerializer(domain_config)
        
        return Response(
            {
                "status": "success",
                "data": serializer.data
            },
            status=status.HTTP_200_OK
        )
    
    except DomainConfiguration.DoesNotExist:
        return Response(
            {
                "status": "error",
                "error": "Domain not found",
                "domain": domain
            },
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['DELETE'])
@require_internal_api_key
def remove_domain(request, domain):
    """
    Remove or deactivate a domain configuration.
    
    DELETE /api/internal/domains/{domain}/
    
    Query params:
    - hard_delete: true to permanently delete, false to just deactivate (default: false)
    
    Response:
    {
        "status": "success",
        "message": "Domain deactivated successfully",
        "domain": "forms.clientbusiness.com"
    }
    """
    try:
        domain_config = DomainConfiguration.objects.get(domain=domain.lower())
        
        hard_delete = request.query_params.get('hard_delete', 'false').lower() == 'true'
        
        if hard_delete:
            domain_config.delete()
            logger.info(f"Permanently deleted domain {domain}")
            message = "Domain permanently deleted"
        else:
            domain_config.is_active = False
            domain_config.save()
            logger.info(f"Deactivated domain {domain}")
            message = "Domain deactivated successfully"
        
        return Response(
            {
                "status": "success",
                "message": message,
                "domain": domain
            },
            status=status.HTTP_200_OK
        )
    
    except DomainConfiguration.DoesNotExist:
        return Response(
            {
                "status": "error",
                "error": "Domain not found",
                "domain": domain
            },
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@require_internal_api_key
def list_account_domains(request, account_id):
    """
    List all domains configured for an account.
    
    GET /api/internal/accounts/{account_id}/domains/
    
    Query params:
    - active_only: true to only show active domains (default: false)
    
    Response:
    {
        "status": "success",
        "account_id": 123,
        "count": 2,
        "domains": [
            {...},
            {...}
        ]
    }
    """
    try:
        active_only = request.query_params.get('active_only', 'false').lower() == 'true'
        
        queryset = DomainConfiguration.objects.filter(account_id=account_id)
        if active_only:
            queryset = queryset.filter(is_active=True)
        
        domains = queryset.order_by('-configured_at')
        serializer = DomainConfigurationSerializer(domains, many=True)
        
        return Response(
            {
                "status": "success",
                "account_id": account_id,
                "count": len(serializer.data),
                "domains": serializer.data
            },
            status=status.HTTP_200_OK
        )
    
    except Exception as e:
        logger.exception(f"Error listing domains for account {account_id}: {str(e)}")
        return Response(
            {
                "status": "error",
                "error": "Internal server error"
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@require_internal_api_key
def update_domain_ssl_status(request, domain):
    """
    Update SSL status for a domain.
    Used by Caddy or monitoring systems to report SSL certificate status.
    
    POST /api/internal/domains/{domain}/ssl-status/
    
    Request Body:
    {
        "ssl_status": "active",  # or "failed", "expired"
        "ssl_issued_at": "2026-02-16T10:00:00Z",  # optional
        "ssl_expires_at": "2026-05-16T10:00:00Z"   # optional
    }
    """
    try:
        domain_config = DomainConfiguration.objects.get(domain=domain.lower())
        
        ssl_status = request.data.get('ssl_status')
        if ssl_status:
            domain_config.ssl_status = ssl_status
        
        ssl_issued_at = request.data.get('ssl_issued_at')
        if ssl_issued_at:
            from django.utils.dateparse import parse_datetime
            domain_config.ssl_issued_at = parse_datetime(ssl_issued_at)
        
        ssl_expires_at = request.data.get('ssl_expires_at')
        if ssl_expires_at:
            from django.utils.dateparse import parse_datetime
            domain_config.ssl_expires_at = parse_datetime(ssl_expires_at)
        
        if ssl_status == 'active':
            domain_config.is_verified = True
        
        domain_config.save()
        
        logger.info(f"Updated SSL status for domain {domain} to {ssl_status}")
        
        serializer = DomainStatusSerializer(domain_config)
        return Response(
            {
                "status": "success",
                "message": "SSL status updated",
                "data": serializer.data
            },
            status=status.HTTP_200_OK
        )
    
    except DomainConfiguration.DoesNotExist:
        return Response(
            {
                "status": "error",
                "error": "Domain not found",
                "domain": domain
            },
            status=status.HTTP_404_NOT_FOUND
        )
