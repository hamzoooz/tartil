#!/bin/bash
# Deployment script for Quran Courses on qurancourses.org
set -e

# Configuration
DOMAIN="qurancourses.org"
WWW_DOMAIN="www.qurancourses.org"
PROJECT_DIR="/home/hamzoooz123/qurancourses/tartil"
USER="hamzoooz123"
GROUP="www-data"
VENV_DIR="$PROJECT_DIR/venv"

echo "========================================="
echo "  Quran Courses Deployment Script"
echo "  Domain: $DOMAIN & $WWW_DOMAIN"
echo "========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Step 1: Check prerequisites
print_status "Step 1/10: Checking prerequisites..."

if ! command -v python3 &> /dev/null; then
    print_error "Python3 is not installed. Please install Python 3.8+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
print_status "Python version: $PYTHON_VERSION"

if ! command -v pip3 &> /dev/null; then
    print_error "pip3 is not installed. Installing..."
    sudo apt-get update && sudo apt-get install -y python3-pip
fi

# Step 2: Create virtual environment
print_status "Step 2/10: Setting up Python virtual environment..."
cd "$PROJECT_DIR"

if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
    print_status "Virtual environment created at $VENV_DIR"
else
    print_status "Virtual environment already exists"
fi

# Step 3: Install requirements
print_status "Step 3/10: Installing Python dependencies..."
source "$VENV_DIR/bin/activate"
pip install --upgrade pip
pip install -r "$PROJECT_DIR/requirements.txt"
print_status "Dependencies installed successfully"

# Step 4: Create necessary directories
print_status "Step 4/10: Creating necessary directories..."
mkdir -p "$PROJECT_DIR/staticfiles"
mkdir -p "$PROJECT_DIR/media"
mkdir -p "$PROJECT_DIR/logs"
print_status "Directories created"

# Step 5: Check/Create .env file
print_status "Step 5/10: Checking environment configuration..."
if [ ! -f "$PROJECT_DIR/.env" ]; then
    print_warning ".env file not found. Creating a default one..."
    cat > "$PROJECT_DIR/.env" << EOF
# Django Secret Key - CHANGE THIS IN PRODUCTION!
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(50))")

# Debug mode - Set to False in production
DEBUG=False

# Allowed hosts
ALLOWED_HOSTS=$DOMAIN,$WWW_DOMAIN,localhost,127.0.0.1
EOF
    print_status ".env file created. Please review and update it if needed."
else
    print_status ".env file exists"
fi

# Step 6: Run Django migrations
print_status "Step 6/10: Running database migrations..."
cd "$PROJECT_DIR"
python manage.py migrate --noinput
print_status "Migrations completed"

# Step 7: Collect static files
print_status "Step 7/10: Collecting static files..."
python manage.py collectstatic --noinput --clear
print_status "Static files collected"

# Step 8: Set proper permissions
print_status "Step 8/10: Setting file permissions..."
chmod -R 755 "$PROJECT_DIR/staticfiles"
chmod -R 775 "$PROJECT_DIR/media"
chmod -R 750 "$PROJECT_DIR"
print_status "Permissions set"

# Step 9: Setup Systemd Service
print_status "Step 9/10: Setting up Systemd service..."

sudo tee /etc/systemd/system/tartil.service > /dev/null <<EOF
[Unit]
Description=Quran Courses LMS Platform
After=network.target

[Service]
User=$USER
Group=$GROUP
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$VENV_DIR/bin"
Environment="DJANGO_SETTINGS_MODULE=tartil.settings"
ExecStart=$VENV_DIR/bin/gunicorn tartil.wsgi:application -c gunicorn.conf.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable tartil
print_status "Systemd service configured"

# Step 10: Setup Nginx
print_status "Step 10/10: Setting up Nginx..."

# Install nginx if not present
if ! command -v nginx &> /dev/null; then
    print_status "Installing Nginx..."
    sudo apt-get update
    sudo apt-get install -y nginx
fi

# Create Nginx configuration
sudo tee /etc/nginx/sites-available/tartil > /dev/null <<EOF
# Nginx configuration for Quran Courses

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
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;
    ssl_session_tickets off;

    # Modern SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # HSTS
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

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
    }
}
EOF

# Enable the site
sudo rm -f /etc/nginx/sites-enabled/default
sudo ln -sf /etc/nginx/sites-available/tartil /etc/nginx/sites-enabled/tartil

# Test Nginx configuration
sudo nginx -t
print_status "Nginx configuration created"

echo ""
echo "========================================="
echo -e "${GREEN}Deployment preparation complete!${NC}"
echo "========================================="
echo ""
echo "Next steps to complete deployment:"
echo ""
echo "1. Setup SSL certificate with Let's Encrypt:"
echo "   sudo apt-get install -y certbot python3-certbot-nginx"
echo "   sudo certbot --nginx -d $DOMAIN -d $WWW_DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN"
echo ""
echo "2. Start the services:"
echo "   sudo systemctl start tartil"
echo "   sudo systemctl restart nginx"
echo ""
echo "3. Check service status:"
echo "   sudo systemctl status tartil"
echo "   sudo systemctl status nginx"
echo ""
echo "4. View logs:"
echo "   sudo journalctl -u tartil -f"
echo "   sudo tail -f /var/log/nginx/tartil_error.log"
echo ""
echo "Your site will be available at: https://$DOMAIN"
echo "========================================="
