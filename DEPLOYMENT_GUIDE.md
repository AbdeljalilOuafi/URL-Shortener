# URL Shortener Centralized Deployment Guide

This guide covers deploying the URL shortener as a centralized service with Caddy for automatic SSL certificate management.

## Architecture Overview

```
┌─────────────────┐         ┌──────────────────────┐
│  Backend API    │────────▶│  URL Shortener       │
│  Server 1..N    │  HTTP   │  (Single Server)     │
│                 │         │                      │
│  - CRM Logic    │         │  - Django App :8000  │
│  - Domain Setup │         │  - Caddy :80, :443   │
│  - Form Emails  │         │  - PostgreSQL        │
└─────────────────┘         │  - On-Demand SSL     │
                             └──────────────────────┘
                                       │
                                       │ HTTPS
                                       ▼
                             ┌──────────────────────┐
                             │  Custom Domains      │
                             │  forms.client1.com   │
                             │  forms.client2.com   │
                             └──────────────────────┘
```

## Prerequisites

- Ubuntu 22.04 LTS or later
- Root or sudo access
- Python 3.11+
- PostgreSQL 14+
- Caddy 2.7+ (will be installed)
- Domain pointed to server IP (e.g., `shorten.hq.coach`)

## Part 1: Server Setup

### 1.1 Update System

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.11 python3.11-venv python3-pip postgresql postgresql-contrib git curl
```

### 1.2 Install Caddy

```bash
# Install Caddy (official method)
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install caddy

# Verify installation
caddy version
```

### 1.3 Create Application User

```bash
sudo useradd -m -s /bin/bash urlshortener
sudo usermod -aG www-data urlshortener
```

## Part 2: Database Setup

### 2.1 Create PostgreSQL Database

```bash
sudo -u postgres psql
```

```sql
CREATE DATABASE urlshortener_db;
CREATE USER urlshortener WITH PASSWORD 'your-secure-password-here';
ALTER ROLE urlshortener SET client_encoding TO 'utf8';
ALTER ROLE urlshortener SET default_transaction_isolation TO 'read committed';
ALTER ROLE urlshortener SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE urlshortener_db TO urlshortener;
ALTER DATABASE urlshortener_db OWNER TO urlshortener;
\q
```

### 2.2 Configure PostgreSQL for Local Connections

```bash
# Allow password authentication for local connections
sudo nano /etc/postgresql/14/main/pg_hba.conf
```

Change:
```
local   all             all                                     peer
```

To:
```
local   all             all                                     md5
```

Restart PostgreSQL:
```bash
sudo systemctl restart postgresql
```

## Part 3: Application Deployment

### 3.1 Clone Repository

```bash
sudo su - urlshortener
cd ~
git clone <your-url-shortener-repo-url> url-shortener
cd url-shortener
```

### 3.2 Create Virtual Environment

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn
```

### 3.3 Configure Environment Variables

```bash
nano .env
```

Add the following:
```env
# Django Settings
SECRET_KEY=your-long-random-secret-key-here-change-this
DEBUG=False
ALLOWED_HOSTS=shorten.hq.coach,*

# Database
DATABASE_URL=postgresql://urlshortener:your-secure-password-here@localhost:5432/urlshortener_db

# Internal API Authentication
INTERNAL_API_KEY=your-secure-internal-api-key-32-chars-minimum

# CORS (allow backend servers)
CORS_ALLOWED_ORIGINS=https://backend.yourdomain.com,https://api.yourdomain.com

# Optional: Rate Limiting
RATE_LIMIT_ENABLED=True
RATE_LIMIT_PER_MINUTE=60
```

**Generate secure keys:**
```bash
# Generate SECRET_KEY
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Generate INTERNAL_API_KEY (32+ characters)
openssl rand -hex 32
```

### 3.4 Run Migrations

```bash
source venv/bin/activate
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput
```

### 3.5 Create Log Directory

```bash
mkdir -p ~/url-shortener/logs
chmod 755 ~/url-shortener/logs
```

## Part 4: Systemd Service Setup

### 4.1 Create Gunicorn Service

```bash
exit  # Exit from urlshortener user
sudo nano /etc/systemd/system/url-shortener.service
```

```ini
[Unit]
Description=URL Shortener Gunicorn Service
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=notify
User=urlshortener
Group=www-data
WorkingDirectory=/home/urlshortener/url-shortener
Environment="PATH=/home/urlshortener/url-shortener/venv/bin"
ExecStart=/home/urlshortener/url-shortener/venv/bin/gunicorn \
    --workers 4 \
    --bind 127.0.0.1:8000 \
    --timeout 30 \
    --access-logfile /home/urlshortener/url-shortener/logs/access.log \
    --error-logfile /home/urlshortener/url-shortener/logs/error.log \
    --log-level info \
    config.wsgi:application

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 4.2 Start Gunicorn Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable url-shortener
sudo systemctl start url-shortener
sudo systemctl status url-shortener
```

Check logs:
```bash
sudo journalctl -u url-shortener -f
```

## Part 5: Caddy Configuration

### 5.1 Copy Caddyfile

```bash
sudo cp /home/urlshortener/url-shortener/Caddyfile /etc/caddy/Caddyfile
```

### 5.2 Update Email in Caddyfile

```bash
sudo nano /etc/caddy/Caddyfile
```

Change `admin@hq.coach` to your email for Let's Encrypt notifications.

### 5.3 Create Caddy Log Directory

```bash
sudo mkdir -p /var/log/caddy
sudo chown caddy:caddy /var/log/caddy
```

### 5.4 Test Caddy Configuration

```bash
sudo caddy validate --config /etc/caddy/Caddyfile
```

### 5.5 Start Caddy

```bash
sudo systemctl enable caddy
sudo systemctl restart caddy
sudo systemctl status caddy
```

Check logs:
```bash
sudo journalctl -u caddy -f
```

## Part 6: Firewall Configuration

```bash
# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow SSH (if not already allowed)
sudo ufw allow 22/tcp

# Enable firewall
sudo ufw enable
sudo ufw status
```

## Part 7: DNS Configuration

### 7.1 Main Domain (shorten.hq.coach)

```
A Record:    shorten.hq.coach  →  YOUR_SERVER_IP
AAAA Record: shorten.hq.coach  →  YOUR_SERVER_IPv6 (optional)
```

### 7.2 Wildcard for Testing (Optional)

```
A Record:    *.shorten.hq.coach  →  YOUR_SERVER_IP
```

### 7.3 Custom Client Domains

Each client domain must be configured by the client:
```
A Record:    forms.clientdomain.com  →  YOUR_SERVER_IP
```

## Part 8: Verification

### 8.1 Test Health Endpoint

```bash
curl https://shorten.hq.coach/health/
```

Expected response:
```json
{"status": "ok", "service": "url-shortener"}
```

### 8.2 Test Internal API (from backend server)

```bash
curl -X POST https://shorten.hq.coach/api/internal/domains/configure/ \
  -H "Content-Type: application/json" \
  -H "X-Internal-API-Key: your-internal-api-key" \
  -d '{
    "domain": "forms.testdomain.com",
    "account_id": 1,
    "domain_type": "forms"
  }'
```

### 8.3 Test Domain SSL

1. Configure a test domain to point to your server IP
2. Call the internal API to register it
3. Visit the domain in a browser: `https://forms.testdomain.com`
4. Verify SSL certificate is automatically issued

## Part 9: Backend Integration

### 9.1 Update Backend Environment Variables

On each backend server, update `.env`:
```env
URL_SHORTENER_API_URL=https://shorten.hq.coach
URL_SHORTENER_INTERNAL_API_KEY=same-key-as-url-shortener
```

### 9.2 Restart Backend Services

```bash
sudo systemctl restart crm-backend
```

### 9.3 Test from Backend

From a backend server Python shell:
```python
from core.services.url_shortener_client import URLShortenerClient

client = URLShortenerClient()

# Test health check
health = client.health_check()
print(health)

# Test domain configuration
result = client.configure_domain(
    domain='forms.testclient.com',
    account_id=123
)
print(result)
```

## Part 10: Monitoring & Maintenance

### 10.1 Monitor Logs

```bash
# URL shortener application logs
sudo journalctl -u url-shortener -f

# Caddy logs
sudo journalctl -u caddy -f
tail -f /var/log/caddy/access.log

# PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-14-main.log
```

### 10.2 Monitor SSL Certificates

```bash
# Check certificate for a domain
echo | openssl s_client -servername forms.testdomain.com -connect YOUR_SERVER_IP:443 2>/dev/null | openssl x509 -noout -dates
```

### 10.3 Database Backups

```bash
# Create backup script
sudo nano /home/urlshortener/backup-db.sh
```

```bash
#!/bin/bash
BACKUP_DIR=/home/urlshortener/backups
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

pg_dump -U urlshortener -h localhost urlshortener_db | gzip > $BACKUP_DIR/urlshortener_db_$DATE.sql.gz

# Keep only last 7 days
find $BACKUP_DIR -name "urlshortener_db_*.sql.gz" -mtime +7 -delete
```

```bash
chmod +x /home/urlshortener/backup-db.sh

# Add to crontab
sudo crontab -e -u urlshortener
```

Add:
```
0 2 * * * /home/urlshortener/backup-db.sh
```

## Part 11: Troubleshooting

### Issue: Caddy not issuing certificates

**Check:** Is domain pointing to server?
```bash
dig forms.testdomain.com
```

**Check:** Can Caddy reach validation endpoint?
```bash
curl http://localhost:8000/caddy/validate-domain?domain=forms.testdomain.com
```

**Check:** Caddy logs for certificate errors:
```bash
sudo journalctl -u caddy --since "10 minutes ago" | grep -i certificate
```

### Issue: 403 Forbidden on domain

**Cause:** Domain not configured in database.

**Fix:** Register domain via internal API or Django admin.

### Issue: Internal API returning 401/403

**Cause:** API key mismatch.

**Fix:** Verify `INTERNAL_API_KEY` matches in both backend and URL shortener `.env` files.

## Security Checklist

- [ ] Strong `SECRET_KEY` generated
- [ ] Strong `INTERNAL_API_KEY` (32+ characters)
- [ ] PostgreSQL password changed from default
- [ ] Firewall configured (only ports 22, 80, 443)
- [ ] `DEBUG=False` in production
- [ ] SSL certificates auto-renewing via Caddy
- [ ] Application logs monitored
- [ ] Database backups automated  
- [ ] Only backend server IPs can call internal API (optional: implement IP allowlist)

## Scaling Considerations

For high traffic:

1. **Increase Gunicorn workers:**
   ```ini
   --workers $((2 * $(nproc) + 1))
   ```

2. **Add Redis caching:**
   ```bash
   pip install django-redis
   ```
   
   Configure in settings.py for session/cache storage.

3. **PostgreSQL connection pooling:**
   ```bash
   pip install psycopg2-binary
   ```

4. **Load balancer** (if multiple URL shortener instances needed):
   - Deploy multiple URL shortener servers
   - Use HAProxy or cloud load balancer
   - Share PostgreSQL database or use replication

## Support

For issues or questions:
- Check logs: `sudo journalctl -u url-shortener -f`
- Django admin: `https://shorten.hq.coach/admin/`
- API docs: `https://shorten.hq.coach/api/docs/` (if DEBUG=True)
