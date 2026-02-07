#!/bin/bash
# Script to setup HTTPS with Let's Encrypt for Tartil

set -e

DOMAIN="tartil.zolna.app"
PROJECT_DIR="/home/ubuntu/hamzoooz/profiles/tartil"

echo "=== Setting up HTTPS for $DOMAIN ==="

# 1. Install required packages
echo "[1/6] Installing Nginx and Certbot..."
sudo apt update
sudo apt install -y nginx certbot python3-certbot-nginx

# 2. Create log directories
echo "[2/6] Creating log directories..."
sudo mkdir -p /var/log/gunicorn
sudo chown ubuntu:www-data /var/log/gunicorn

# 3. Collect static files
echo "[3/6] Collecting static files..."
cd $PROJECT_DIR
source venv/bin/activate
python manage.py collectstatic --noinput

# 4. Setup Gunicorn service
echo "[4/6] Setting up Gunicorn service..."
sudo cp $PROJECT_DIR/deploy/gunicorn.service /etc/systemd/system/tartil.service
sudo systemctl daemon-reload
sudo systemctl enable tartil
sudo systemctl start tartil

# 5. Setup Nginx (without SSL first)
echo "[5/6] Setting up Nginx..."
sudo tee /etc/nginx/sites-available/tartil > /dev/null <<EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;

    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    location /static/ {
        alias $PROJECT_DIR/staticfiles/;
    }

    location /media/ {
        alias $PROJECT_DIR/media/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/tartil /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

# 6. Get SSL certificate
echo "[6/6] Obtaining SSL certificate..."
sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN

echo ""
echo "=== HTTPS Setup Complete! ==="
echo "Your site is now available at: https://$DOMAIN"
echo ""
echo "Useful commands:"
echo "  sudo systemctl status tartil     # Check Gunicorn status"
echo "  sudo systemctl restart tartil    # Restart Gunicorn"
echo "  sudo nginx -t                    # Test Nginx config"
echo "  sudo systemctl restart nginx     # Restart Nginx"
echo "  sudo certbot renew --dry-run     # Test certificate renewal"
