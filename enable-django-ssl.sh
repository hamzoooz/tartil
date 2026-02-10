#!/bin/bash
# Enable SSL/HTTPS settings in Django

PROJECT_DIR="/home/hamzoooz123/qurancourses/tartil"
SETTINGS_FILE="$PROJECT_DIR/tartil/settings.py"

echo "Enabling Django SSL settings..."

# Uncomment SSL settings
sed -i "s/# SECURE_SSL_REDIRECT = True/SECURE_SSL_REDIRECT = True/g" $SETTINGS_FILE
sed -i "s/# SESSION_COOKIE_SECURE = True/SESSION_COOKIE_SECURE = True/g" $SETTINGS_FILE
sed -i "s/# CSRF_COOKIE_SECURE = True/CSRF_COOKIE_SECURE = True/g" $SETTINGS_FILE
sed -i "s/# SECURE_HSTS_SECONDS = 31536000/SECURE_HSTS_SECONDS = 31536000/g" $SETTINGS_FILE
sed -i "s/# SECURE_HSTS_INCLUDE_SUBDOMAINS = True/SECURE_HSTS_INCLUDE_SUBDOMAINS = True/g" $SETTINGS_FILE
sed -i "s/# SECURE_HSTS_PRELOAD = True/SECURE_HSTS_PRELOAD = True/g" $SETTINGS_FILE

echo "SSL settings enabled in Django."
echo "Restarting tartil service..."
sudo systemctl restart tartil

echo "Done! Django is now configured for HTTPS."
