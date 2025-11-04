# API Quick Reference

## Base URL
- Development: `http://localhost:8001`
- Production: `https://your-domain.com`

## Authentication
**None required** - This is a public API (like bit.ly)

## Endpoints

### 1. Create Short URL

```http
POST /api/shorten/
Content-Type: application/json

{
  "original_url": "https://example.com/very/long/url",
  "title": "My Link",              // Optional
  "short_code": "custom",          // Optional - auto-generated if not provided
  "domain": "pay.company.com",     // Optional - auto-detected from request
  "expires_at": "2025-12-31T23:59:59Z"  // Optional
}
```

**Response (201 Created):**
```json
{
  "status": "success",
  "data": {
    "id": 1,
    "short_code": "abc123",
    "original_url": "https://example.com/very/long/url",
    "domain": "pay.company.com",
    "full_short_url": "https://pay.company.com/abc123",
    "title": "My Link",
    "clicks": 0,
    "is_active": true,
    "is_expired": false,
    "created_at": "2025-11-04T10:30:00Z",
    "updated_at": "2025-11-04T10:30:00Z",
    "expires_at": null
  }
}
```

### 2. Redirect to Original URL

```http
GET /{short_code}/
```

**Response:** `302 Redirect` to original URL

### 3. List URLs for Domain

```http
GET /api/urls/?limit=10&offset=0&search=payment&is_active=true
```

**Query Parameters:**
- `limit` (default: 50) - Number of results
- `offset` (default: 0) - Pagination offset
- `search` - Search in title or original_url
- `is_active` - Filter by active status (true/false)

**Response (200 OK):**
```json
{
  "count": 150,
  "results": [
    {
      "id": 1,
      "short_code": "abc123",
      "full_short_url": "https://pay.company.com/abc123",
      ...
    }
  ]
}
```

### 4. Get URL Statistics

```http
GET /api/stats/{short_code}/
```

**Response (200 OK):**
```json
{
  "short_url": {
    "id": 1,
    "short_code": "abc123",
    "clicks": 150,
    ...
  },
  "total_clicks": 150,
  "recent_clicks": [
    {
      "clicked_at": "2025-11-04T10:30:00Z",
      "country": "US",
      "referer": "https://google.com"
    }
  ],
  "clicks_by_day": {
    "2025-11-01": 45,
    "2025-11-02": 62,
    "2025-11-03": 43
  },
  "clicks_by_country": {
    "US": 89,
    "CA": 31,
    "UK": 30
  }
}
```

### 5. Update Short URL

```http
PATCH /api/urls/{short_code}/
Content-Type: application/json

{
  "title": "New Title",
  "is_active": false,
  "expires_at": "2025-12-31T23:59:59Z"
}
```

**Response (200 OK):** Updated URL object

### 6. Delete (Deactivate) Short URL

```http
DELETE /api/urls/{short_code}/
```

**Response:** `204 No Content`

### 7. Health Check

```http
GET /health/
```

**Response (200 OK):**
```json
{
  "status": "ok",
  "service": "url-shortener"
}
```

### 8. API Information

```http
GET /api/
```

**Response (200 OK):**
```json
{
  "service": "URL Shortener",
  "version": "1.0.0",
  "endpoints": {
    "create_short_url": "/api/shorten/",
    "list_urls": "/api/urls/",
    "get_stats": "/api/stats/{short_code}/",
    "redirect": "/{short_code}/"
  },
  "docs": "/api/docs/"
}
```

## Interactive Documentation

Visit `/api/docs/` for Swagger UI or `/api/redoc/` for ReDoc documentation.

## Examples

### cURL Examples

```bash
# Create short URL
curl -X POST http://localhost:8001/api/shorten/ \
  -H "Content-Type: application/json" \
  -d '{
    "original_url": "https://checkout.stripe.com/pay/cs_test_abc123",
    "title": "Payment Link"
  }'

# Get statistics
curl http://localhost:8001/api/stats/abc123/

# List all URLs for current domain
curl http://localhost:8001/api/urls/

# Update URL
curl -X PATCH http://localhost:8001/api/urls/abc123/ \
  -H "Content-Type: application/json" \
  -d '{"title": "Updated Title"}'

# Delete URL
curl -X DELETE http://localhost:8001/api/urls/abc123/
```

### Python Example

```python
import requests

# Create short URL
response = requests.post('http://localhost:8001/api/shorten/', json={
    'original_url': 'https://example.com/very/long/url',
    'title': 'My Link'
})
data = response.json()
short_url = data['data']['full_short_url']
print(f"Short URL: {short_url}")

# Get statistics
stats = requests.get(f'http://localhost:8001/api/stats/abc123/').json()
print(f"Total clicks: {stats['total_clicks']}")
```

### JavaScript Example

```javascript
// Create short URL
const response = await fetch('http://localhost:8001/api/shorten/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    original_url: 'https://example.com/very/long/url',
    title: 'My Link'
  })
});

const data = await response.json();
console.log('Short URL:', data.data.full_short_url);

// Get statistics
const stats = await fetch('http://localhost:8001/api/stats/abc123/')
  .then(r => r.json());
console.log('Total clicks:', stats.total_clicks);
```

## Error Responses

### 400 Bad Request
```json
{
  "original_url": ["This field is required."]
}
```

### 404 Not Found
```json
{
  "detail": "Not found."
}
```

### 410 Gone (Expired Link)
```html
<h1>Link Expired</h1>
<p>This link has expired and is no longer valid.</p>
```

## Rate Limiting

Currently not enforced. Can be enabled via environment variables:
```
RATE_LIMIT_ENABLED=True
RATE_LIMIT_PER_MINUTE=60
```

## CORS

CORS is enabled by default for common development origins. Configure via `CORS_ALLOWED_ORIGINS` in `.env`.
