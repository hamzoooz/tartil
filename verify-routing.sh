#!/bin/bash
# Verify Nginx routing is correct

echo "========================================="
echo "  Verifying Nginx Routing"
echo "========================================="
echo ""

echo "1. Checking Nginx configuration files..."
echo "-----------------------------------------"
echo ""

echo "=== tartil config (should proxy to port 8005) ==="
grep -E "(server_name|proxy_pass|listen)" /etc/nginx/sites-available/tartil 2>/dev/null | head -10
echo ""

echo "=== abaqalanaqa config (should proxy to port 8000) ==="
grep -E "(server_name|proxy_pass|listen)" /etc/nginx/sites-available/abaqalanaqa 2>/dev/null | head -10
echo ""

echo "2. Checking which ports are listening..."
echo "-----------------------------------------"
ss -tlnp | grep -E "(8000|8005)" || netstat -tlnp 2>/dev/null | grep -E "(8000|8005)"
echo ""

echo "3. Checking service status..."
echo "-----------------------------------------"
echo "tartil service:"
systemctl is-active tartil 2>/dev/null || echo "  Status: unknown"
echo ""
echo "abaqalanaqa service:"
systemctl is-active abaqalanaqa 2>/dev/null || echo "  Status: unknown (may use different service name)"
echo ""

echo "4. Testing HTTP routing..."
echo "-----------------------------------------"
echo "Testing qurancourses.org:80 ->"
curl -s -I http://qurancourses.org 2>&1 | head -3
echo ""

echo "5. Nginx test configuration..."
echo "-----------------------------------------"
sudo nginx -t 2>&1
echo ""

echo "========================================="
echo "  Verification Complete"
echo "========================================="
