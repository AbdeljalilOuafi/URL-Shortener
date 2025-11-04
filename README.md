# URL Shortener - Standalone Service

A multi-domain URL shortening service that allows clients to use their own subdomains without manual server configuration.

## Features

- **Multi-domain Support**: Clients can use any subdomain (e.g., `pay.clientcompany.com`)
- **Wildcard Subdomain Configuration**: Automatically accepts any subdomain
- **Public API**: No authentication required (like bit.ly)
- **Click Analytics**: Track clicks, countries, referers
- **REST API**: Full CRUD operations for URL management
- **Admin Interface**: Django admin for managing clients and URLs
- **Docker Support**: Easy deployment with Docker and docker-compose

## How It Works

1. **Client Setup**: Point your subdomain to our server IP (DNS A record)
2. **Instant Access**: Start using the API immediately - no waiting!
3. **URL Creation**: POST to `/api/shorten/` to create short URLs
4. **Redirection**: GET `/{short_code}/` redirects to original URL

### Example Client Flow

```bash
# 1. Client points pay.clientcompany.com to our server (DNS)
# 2. Immediately create short URLs:

curl -X POST https://pay.clientcompany.com/api/shorten/ \
  -H "Content-Type: application/json" \
  -d '{
    "original_url": "https://checkout.stripe.com/pay/cs_test_...",
    "title": "Payment Link"
  }'

# Response:
{
  "status": "success",
  "data": {
    "id": 1,
    "short_code": "abc123",
    "full_short_url": "https://pay.clientcompany.com/abc123",
    "original_url": "https://checkout.stripe.com/...",
    "clicks": 0
  }
}

# 3. Share the short URL: https://pay.clientcompany.com/abc123
```

## Quick Start

### Development Setup

1. **Clone and setup**:
```bash
git clone <repository-url>
cd URL-Shortener
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your settings
```

3. **Run migrations**:
```bash
python manage.py migrate
python manage.py createsuperuser
```

4. **Start development server**:
```bash
python manage.py runserver 8001
```

5. **Test the API**:
```bash
# Create a short URL
curl -X POST http://localhost:8001/api/shorten/ \
  -H "Content-Type: application/json" \
  -d '{"original_url": "https://example.com"}'

# Access the short URL
curl -I http://localhost:8001/abc123/
```

### Docker Deployment

1. **Using docker-compose** (recommended):
```bash
docker-compose up -d
```

2. **Access the service**:
- API: http://localhost:8001
- Admin: http://localhost:8001/admin
- Docs: http://localhost:8001/api/docs/

### Production Deployment

1. **Configure environment variables**:
```bash
# Required for production
SECRET_KEY=your-secret-key-here
DEBUG=False
DATABASE_URL=postgresql://user:pass@localhost:5432/db
ALLOWED_HOSTS=your-domain.com,*.your-domain.com
```

2. **Setup Nginx** (wildcard subdomain support):
```nginx
server {
    listen 80;
    server_name ~^(?<subdomain>.+)\.your-domain\.com$;
    
    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

3. **SSL Setup**:
```bash
# Get wildcard SSL certificate for *.your-domain.com
certbot certonly --manual --preferred-challenges dns \
  -d *.your-domain.com -d your-domain.com
```

## API Documentation

### Create Short URL
```http
POST /api/shorten/
Content-Type: application/json

{
  "original_url": "https://example.com/very/long/url",
  "title": "Optional title",
  "short_code": "custom123",  // Optional
  "expires_at": "2024-12-31T23:59:59Z"  // Optional
}
```

### Get URL Statistics
```http
GET /api/stats/{short_code}/
```

### List URLs for Domain
```http
GET /api/urls/?limit=10&offset=0&search=payment
```

### Redirect (Public)
```http
GET /{short_code}/
# Returns 302 redirect to original URL
```

### API Documentation
Visit `/api/docs/` for interactive Swagger documentation.

## Client Management

### Auto-created Clients
When a request comes from a new domain, a client is automatically created:
- Name: "Client for {domain}"
- Email: "admin@{domain}"
- API Key: Auto-generated

### Manual Client Creation
Use Django admin at `/admin/` to manually create and manage clients.

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | Generated | Django secret key |
| `DEBUG` | `True` | Debug mode |
| `DATABASE_URL` | SQLite | Database connection |
| `ALLOWED_HOSTS` | `*` | Allowed hostnames |
| `CORS_ALLOWED_ORIGINS` | Default list | CORS allowed origins |
| `ALLOWED_SHORT_URL_DOMAINS` | Empty (all) | Restrict domains |
| `RATE_LIMIT_ENABLED` | `False` | Enable rate limiting |

### Security Considerations

- **Isolated Service**: Runs separately from main applications
- **Rate Limiting**: Configurable to prevent abuse
- **Domain Validation**: Optional domain whitelist
- **Click Analytics**: Monitor for malicious patterns
- **No Authentication**: Public API by design (like bit.ly)

## Analytics & Monitoring

### Click Analytics
- IP addresses (anonymized in production)
- User agents
- Referers
- Geographic data (optional GeoIP2)
- Timestamps

### Usage Monitoring
- Track URLs created per domain
- Monitor click patterns
- Set usage limits per client

## Development

### Project Structure
```
url_shortener/
├── models.py      # Client, ShortURL, ClickAnalytics
├── views.py       # API endpoints
├── serializers.py # DRF serializers
├── urls.py        # URL routing
├── admin.py       # Django admin
└── middleware.py  # Multi-domain middleware
```

### Testing
```bash
python manage.py test
```

### Database Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

## Troubleshooting

### Common Issues

1. **Domain not working**: Check DNS A record points to server IP
2. **CORS errors**: Add domain to `CORS_ALLOWED_ORIGINS`
3. **SSL issues**: Ensure wildcard certificate covers subdomain
4. **Performance**: Add Redis caching for high traffic

### Health Check
```bash
curl http://your-domain.com/health/
# Should return: {"status": "ok", "service": "url-shortener"}
```

## License

MIT License - see LICENSE file for details.

## Support

For issues and questions, please create an issue in the repository.
