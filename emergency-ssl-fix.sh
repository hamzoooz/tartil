#!/bin/bash
# Emergency SSL Fix for qurancourses.org
# Run: sudo bash emergency-ssl-fix.sh

set -e

echo "========================================="
echo "  Emergency SSL Fix"
echo "========================================="
echo ""

if [ "$EUID" -ne 0 ]; then 
    echo "ERROR: Please run as root: sudo bash emergency-ssl-fix.sh"
    exit 1
fi

# Step 1: Get SSL certificate for qurancourses.org
echo "[1/4] Getting SSL certificate for qurancourses.org..."
if [ ! -d "/etc/letsencrypt/live/qurancourses.org" ]; then
    certbot certonly --standalone -d qurancourses.org -d www.qurancourses.org --non-interactive --agree-tos --email admin@qurancourses.org
fi

# Step 2: Fix Nginx config
echo "[2/4] Updating Nginx configuration..."
cat > /etc/nginx/sites-available/tartil << 'EOF'
server {
    listen 80;
    server_name qurancourses.org www.qurancourses.org;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name qurancourses.org www.qurancourses.org;
    
    ssl_certificate /etc/letsencrypt/live/qurancourses.org/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/qurancourses.org/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;
    
    add_header Strict-Transport-Security "max-age=63072000" always;
    add_header X-Frame-Options "SAMEORIGIN" always;

    location /static/ {
        alias /home/hamzoooz123/qurancourses/tartil/staticfiles/;
        expires 30d;
    }

    location /media/ {
        alias /home/hamzoooz123/qurancourses/tartil/media/;
        expires 7d;
    }

    location / {
        proxy_pass http://127.0.0.1:8005;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 300s;
        proxy_read_timeout 300s;
    }
}
EOF

# Step 3: Fix abaqalanaqa config to NOT catch qurancourses.org
echo "[3/4] Fixing abaqalanaqa config..."
if [ -f /etc/nginx/sites-available/abaqalanaqa ]; then
    # Comment out any default server or catch-all that might be grabbing qurancourses.org
    sed -i 's/listen 443 ssl http2;/listen 443 ssl http2;/g' /etc/nginx/sites-available/abaqalanaqa
    sed -i 's/server_name _;/server_name abaqalanaqa.qa www.abaqalanaqa.qa;/g' /etc/nginx/sites-available/abaqalanaqa
fi

# Step 4: Test and reload
echo "[4/4] Testing and reloading Nginx..."
nginx -t
systemctl reload nginx

echo ""
echo "========================================="
echo "  SSL Fix Complete!"
echo "========================================="
echo ""
echo "Test with:"
echo "  curl -I https://qurancourses.org"
echo ""
