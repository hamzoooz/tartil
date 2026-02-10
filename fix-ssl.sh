#!/bin/bash
# Fix SSL for qurancourses.org
set -e

DOMAIN="qurancourses.org"
WWW_DOMAIN="www.qurancourses.org"
EMAIL="${1:-admin@qurancourses.org}"

echo "========================================="
echo "  Fixing SSL for $DOMAIN"
echo "========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "ERROR: Please run as root: sudo bash fix-ssl.sh"
    exit 1
fi

# Install certbot if needed
if ! command -v certbot &> /dev/null; then
    echo "Installing Certbot..."
    apt-get update
    apt-get install -y certbot python3-certbot-nginx
fi

# Check if certificate exists for qurancourses.org
if [ -d "/etc/letsencrypt/live/$DOMAIN" ]; then
    echo "Certificate exists for $DOMAIN"
else
    echo "Getting new certificate for $DOMAIN..."
    certbot certonly --nginx -d $DOMAIN -d $WWW_DOMAIN --non-interactive --agree-tos --email $EMAIL
fi

# Create proper Nginx config with SSL
cat > /etc/nginx/sites-available/tartil << EOF
# HTTP - Redirect to HTTPS
server {
    listen 80;
    server_name $DOMAIN $WWW_DOMAIN;
    return 301 https://\$host\$request_uri;
}

# HTTPS Server
server {
    listen 443 ssl http2;
    server_name $DOMAIN $WWW_DOMAIN;
    
    client_max_body_size 50M;

    # SSL (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    
    # Modern SSL
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=63072000" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

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

    # Proxy to Gunicorn
    location / {
        proxy_pass http://127.0.0.1:8005;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Forwarded-Host \$host;
        proxy_set_header X-Forwarded-Port \$server_port;
        proxy_redirect off;
        proxy_connect_timeout 300s;
        proxy_read_timeout 300s;
    }
}
EOF

echo "Nginx configuration updated"

# Test Nginx config
nginx -t

# Reload Nginx
echo "Reloading Nginx..."
systemctl reload nginx

echo ""
echo "========================================="
echo "  SSL Fixed!"
echo "========================================="
echo ""
echo "Your site should now work at:"
echo "  https://$DOMAIN"
echo ""
echo "Certificate info:"
certbot certificates | grep -A5 "$DOMAIN"
echo ""
