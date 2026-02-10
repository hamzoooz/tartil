#!/bin/bash
#
# Deploy Script for Quran Courses Platform
# Deploys to: https://qurancourses.org
#

set -e

PROJECT_DIR="/home/hamzoooz123/qurancourses/tartil"
VENV_DIR="$PROJECT_DIR/venv"
USER="hamzoooz123"
NGINX_CONFIG="/etc/nginx/sites-available/tartil"

echo "=========================================="
echo "🚀 Deploying Quran Courses Platform"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Navigate to project directory
cd $PROJECT_DIR

# Activate virtual environment
print_status "Activating virtual environment..."
source $VENV_DIR/bin/activate

# Install/update requirements
print_status "Installing requirements..."
pip install -q -r requirements.txt

# Run migrations
print_status "Running database migrations..."
python manage.py migrate --noinput

# Collect static files
print_status "Collecting static files..."
python manage.py collectstatic --noinput --clear

# Initialize webhook endpoints (if not exists)
print_status "Initializing webhook endpoints..."
python manage.py init_webhook_endpoints || true

# Test Django check
print_status "Running Django system check..."
python manage.py check --deploy || print_warning "Django check warnings found"

# Restart Gunicorn (send HUP signal to gracefully reload)
print_status "Reloading Gunicorn..."
MASTER_PID=$(pgrep -f "gunicorn tartil.wsgi" | head -1)
if [ -n "$MASTER_PID" ]; then
    kill -HUP $MASTER_PID
    print_status "Gunicorn reloaded (PID: $MASTER_PID)"
else
    print_error "Gunicorn master process not found!"
    print_warning "Starting Gunicorn manually..."
    gunicorn tartil.wsgi:application -c gunicorn.conf.py
fi

# Reload Nginx (requires sudo)
if sudo -n true 2>/dev/null; then
    print_status "Reloading Nginx..."
    sudo nginx -t && sudo systemctl reload nginx
else
    print_warning "Skipping Nginx reload (sudo access required)"
    print_warning "Run manually: sudo nginx -t && sudo systemctl reload nginx"
fi

# Verify deployment
print_status "Verifying deployment..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8005/ || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
    print_status "✅ Deployment successful! (HTTP 200)"
else
    print_error "❌ Deployment verification failed (HTTP $HTTP_CODE)"
fi

echo ""
echo "=========================================="
echo "🎉 Deployment Complete!"
echo "=========================================="
echo ""
echo "Website URLs:"
echo "  - https://qurancourses.org"
echo "  - https://www.qurancourses.org"
echo ""
echo "Dashboard:"
echo "  - https://qurancourses.org/dashboard/"
echo ""
echo "Notification System:"
echo "  - https://qurancourses.org/notifications-system/"
echo ""
