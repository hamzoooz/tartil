#!/bin/bash
# Fix Nginx routing - Ensure qurancourses.org routes to tartil (port 8005)
# not abaqalanaqa (port 8000)

set -e

echo "========================================="
echo "  Fixing Nginx Routing for qurancourses.org"
echo "========================================="
echo ""

if [ "$EUID" -ne 0 ]; then 
    echo "ERROR: Please run as root: sudo bash fix-nginx-routing.sh"
    exit 1
fi

# Backup current configs
echo "Backing up current Nginx configs..."
cp /etc/nginx/sites-available/tartil /etc/nginx/sites-available/tartil.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null || true
cp /etc/nginx/sites-available/abaqalanaqa /etc/nginx/sites-available/abaqalanaqa.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null || true

# Create the correct Nginx config for tartil (qurancourses.org)
echo "Creating Nginx config for qurancourses.org -> tartil (port 8005)..."

cat > /etc/nginx/sites-available/tartil << 'EOF'
# Nginx configuration for Quran Courses (tartil)
# This server handles qurancourses.org

# HTTP - Redirect to HTTPS
server {
    listen 80;
    server_name qurancourses.org www.qurancourses.org;
    
    # Allow Let's Encrypt validation
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
    
    return 301 https://$host$request_uri;
}

# HTTPS Server for qurancourses.org
server {
    listen 443 ssl http2;
    server_name qurancourses.org www.qurancourses.org;
    
    client_max_body_size 50M;

    # SSL Certificate
    ssl_certificate /etc/letsencrypt/live/qurancourses.org/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/qurancourses.org/privkey.pem;
    
    # Modern SSL configuration
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
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

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

    # Proxy to Gunicorn on port 8005 (tartil)
    location / {
        proxy_pass http://127.0.0.1:8005;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Port $server_port;
        proxy_redirect off;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
}
EOF

# Make sure abaqalanaqa config only handles its own domain
echo "Updating abaqalanaqa config to only handle abaqalanaqa.qa..."

if [ -f /etc/nginx/sites-available/abaqalanaqa ]; then
    # Extract the server blocks and rewrite them properly
    cat > /etc/nginx/sites-available/abaqalanaqa << 'EOF'
upstream django_backend {
    server 127.0.0.1:8000;
    keepalive 32;
}

# HTTP - Redirect to HTTPS (only for abaqalanaqa.qa)
server {
    listen 80;
    server_name abaqalanaqa.qa www.abaqalanaqa.qa;
    client_max_body_size 50M;
    return 301 https://$server_name$request_uri;
}

# HTTPS Server (only for abaqalanaqa.qa)
server {
    listen 443 ssl http2;
    server_name abaqalanaqa.qa www.abaqalanaqa.qa;
    client_max_body_size 50M;

    # SSL (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/abaqalanaqa.qa/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/abaqalanaqa.qa/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;
    
    add_header Strict-Transport-Security "max-age=63072000" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;

    # Admin paths
    location ~ ^/(admin|admin-dashboard|admin-products|admin-orders|admin-pos|admin-finance)/ {
        proxy_pass http://django_backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Port $server_port;
        proxy_redirect off;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # API paths
    location ~ ^/(api|accounts|auth|cart|orders|products|shop-api)/ {
        proxy_pass http://django_backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Port $server_port;
        proxy_redirect off;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Static files
    location /static/ {
        alias /home/hamzoooz123/abaq-alanaqa/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Media files
    location /media/ {
        alias /home/hamzoooz123/abaq-alanaqa/media/;
        expires 7d;
    }

    # React frontend - catch all
    location / {
        root /home/hamzoooz123/abaq-alanaqa/frontend/build;
        try_files $uri $uri/ /index.html;
        add_header Cache-Control "no-cache";
    }
}
EOF
fi

# Enable both sites
echo "Enabling both sites..."
ln -sf /etc/nginx/sites-available/tartil /etc/nginx/sites-enabled/tartil 2>/dev/null || true
ln -sf /etc/nginx/sites-available/abaqalanaqa /etc/nginx/sites-enabled/abaqalanaqa 2>/dev/null || true

# Remove default if it exists
rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
echo "Testing Nginx configuration..."
nginx -t

# Reload Nginx
echo "Reloading Nginx..."
systemctl reload nginx

echo ""
echo "========================================="
echo "  Nginx Routing Fixed!"
echo "========================================="
echo ""
echo "qurancourses.org -> tartil (port 8005)"
echo "abaqalanaqa.qa   -> abaqalanaqa (port 8000)"
echo ""
echo "Test the sites:"
echo "  https://qurancourses.org"
echo "  https://abaqalanaqa.qa"
echo ""
