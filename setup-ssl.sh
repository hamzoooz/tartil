#!/bin/bash
# SSL Setup Script for Quran Courses
# Usage: sudo bash setup-ssl.sh [email]

set -e

DOMAIN="qurancourses.org"
WWW_DOMAIN="www.qurancourses.org"
EMAIL="${1:-admin@qurancourses.org}"
PROJECT_DIR="/home/hamzoooz123/qurancourses/tartil"

echo "========================================="
echo "  SSL Certificate Setup for $DOMAIN"
echo "========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    print_error "Please run as root: sudo bash setup-ssl.sh"
    exit 1
fi

# Install certbot if not present
if ! command -v certbot &> /dev/null; then
    print_status "Installing Certbot..."
    apt-get update
    apt-get install -y certbot python3-certbot-nginx
fi

# Check if certificate already exists
if [ -d "/etc/letsencrypt/live/$DOMAIN" ]; then
    print_warning "Certificate already exists for $DOMAIN"
    read -p "Do you want to renew/replace it? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_status "Skipping certificate generation"
        exit 0
    fi
fi

# Obtain SSL certificate
print_status "Requesting SSL certificate for $DOMAIN and $WWW_DOMAIN..."
certbot --nginx -d $DOMAIN -d $WWW_DOMAIN --non-interactive --agree-tos --email $EMAIL

# Test certificate renewal
print_status "Testing automatic renewal..."
certbot renew --dry-run

print_status "SSL certificate installed successfully!"

# Update Nginx configuration to force HTTPS
print_status "Updating Nginx configuration for HTTPS..."

cat > /etc/nginx/sites-available/tartil << 'EOF'
# Nginx configuration for Quran Courses with SSL

# HTTP: Redirect all to HTTPS
server {
    listen 80;
    server_name qurancourses.org www.qurancourses.org;
    
    # Allow Let's Encrypt validation
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
    
    # Redirect all HTTP to HTTPS
    return 301 https://$host$request_uri;
}

# HTTPS: qurancourses.org
server {
    listen 443 ssl http2;
    server_name qurancourses.org www.qurancourses.org;

    # SSL Configuration (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/qurancourses.org/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/qurancourses.org/privkey.pem;
    
    # Modern SSL configuration
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;
    ssl_session_tickets off;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # HSTS (uncomment after confirming HTTPS works)
    # add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Logs
    access_log /var/log/nginx/tartil_access.log;
    error_log /var/log/nginx/tartil_error.log;

    # Max upload size
    client_max_body_size 50M;

    # Static files
    location /static/ {
        alias /home/hamzoooz123/qurancourses/tartil/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Media files
    location /media/ {
        alias /home/hamzoooz123/qurancourses/tartil/media/;
        expires 7d;
    }

    # Gunicorn proxy
    location / {
        proxy_pass http://127.0.0.1:8005;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 300s;
        proxy_read_timeout 300s;
        proxy_redirect off;
    }
}
EOF

# Test Nginx configuration
print_status "Testing Nginx configuration..."
nginx -t

# Restart Nginx
print_status "Restarting Nginx..."
systemctl restart nginx

echo ""
echo "========================================="
echo -e "${GREEN}HTTPS Setup Complete!${NC}"
echo "========================================="
echo ""
echo "Your site is now available at:"
echo "  https://$DOMAIN"
echo "  https://$WWW_DOMAIN"
echo ""
echo "SSL Certificate Info:"
echo "  sudo certbot certificates"
echo ""
echo "Auto-renewal is enabled. Test with:"
echo "  sudo certbot renew --dry-run"
echo ""
echo "========================================="
