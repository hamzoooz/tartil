#!/bin/bash
# SSL Setup script for Quran Courses on qurancourses.org
set -e

DOMAIN="qurancourses.org"
WWW_DOMAIN="www.qurancourses.org"
EMAIL="${1:-admin@qurancourses.org}"

echo "========================================="
echo "  SSL Certificate Setup for Quran Courses"
echo "  Domain: $DOMAIN & $WWW_DOMAIN"
echo "  Email: $EMAIL"
echo "========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Install Certbot
print_status "Installing Certbot..."
if ! command -v certbot &> /dev/null; then
    sudo apt-get update
    sudo apt-get install -y certbot python3-certbot-nginx
fi

# Create webroot for ACME challenges
sudo mkdir -p /var/www/html/.well-known/acme-challenge
sudo chown -R $USER:$USER /var/www/html

# Temporarily start Nginx for HTTP validation
print_status "Preparing Nginx for certificate request..."

# Create temporary HTTP-only config
sudo tee /etc/nginx/sites-available/tartil > /dev/null <<EOF
server {
    listen 80;
    server_name $DOMAIN $WWW_DOMAIN;

    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    location / {
        return 200 "OK - Certificate setup in progress";
        add_header Content-Type text/plain;
    }
}
EOF

sudo nginx -t && sudo systemctl restart nginx

# Request certificate
print_status "Requesting SSL certificate from Let's Encrypt..."
sudo certbot certonly --webroot \
    -w /var/www/html \
    -d $DOMAIN \
    -d $WWW_DOMAIN \
    --non-interactive \
    --agree-tos \
    --email $EMAIL \
    --rsa-key-size 4096

print_status "SSL certificate obtained successfully!"

# Update Nginx config with SSL
print_status "Updating Nginx configuration with SSL..."

PROJECT_DIR="/home/hamzoooz123/qurancourses/tartil"

sudo tee /etc/nginx/sites-available/tartil > /dev/null <<EOF
# Nginx configuration for Quran Courses - HTTPS Enabled

# HTTP: Redirect all to HTTPS
server {
    listen 80;
    server_name $DOMAIN $WWW_DOMAIN;

    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    return 301 https://\$host\$request_uri;
}

# HTTPS: qurancourses.org
server {
    listen 443 ssl http2;
    server_name $DOMAIN $WWW_DOMAIN;

    # SSL Configuration (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    ssl_trusted_certificate /etc/letsencrypt/live/$DOMAIN/chain.pem;
    
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;
    ssl_session_tickets off;

    # Modern SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # OCSP Stapling
    ssl_stapling on;
    ssl_stapling_verify on;

    # HSTS
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;

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
        alias $PROJECT_DIR/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    # Media files
    location /media/ {
        alias $PROJECT_DIR/media/;
        expires 7d;
    }

    # Gunicorn proxy
    location / {
        proxy_pass http://127.0.0.1:8005;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 300s;
        proxy_read_timeout 300s;
        proxy_buffering off;
    }
}
EOF

# Test and reload Nginx
sudo nginx -t && sudo systemctl restart nginx

# Setup auto-renewal
print_status "Setting up certificate auto-renewal..."
if ! sudo crontab -l | grep -q "certbot renew"; then
    (sudo crontab -l 2>/dev/null; echo "0 3 * * * certbot renew --quiet --deploy-hook 'systemctl reload nginx'") | sudo crontab -
    print_status "Auto-renewal cron job added"
fi

# Start the Django application
print_status "Starting Quran Courses service..."
sudo systemctl start tartil || sudo systemctl restart tartil

echo ""
echo "========================================="
echo -e "${GREEN}SSL Setup Complete!${NC}"
echo "========================================="
echo ""
echo "Your site is now available at:"
echo "  - https://$DOMAIN"
echo "  - https://$WWW_DOMAIN"
echo ""
echo "Certificate will auto-renew via cron."
echo "To test renewal: sudo certbot renew --dry-run"
echo "========================================="
