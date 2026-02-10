# HTTPS/SSL Setup Guide for إدارة الدورات القرآنية

This guide will help you enable HTTPS for your Quran Courses platform.

## Prerequisites

- Domain name (qurancourses.org) pointing to your server IP
- Server running on port 80 (HTTP)
- Root/sudo access

## Step 1: Obtain SSL Certificate

Run the SSL setup script with sudo:

```bash
cd /home/hamzoooz123/qurancourses/tartil
sudo bash setup-ssl.sh admin@qurancourses.org
```

This script will:
1. Install Certbot (if not already installed)
2. Request SSL certificates from Let's Encrypt
3. Update Nginx configuration for HTTPS
4. Set up automatic renewal

## Step 2: Verify HTTPS Works

After running the script, visit:
- https://qurancourses.org
- https://www.qurancourses.org

You should see the green lock icon in your browser.

## Step 3: Enable Django SSL Settings

Once HTTPS is confirmed working, enable Django's security features:

```bash
cd /home/hamzoooz123/qurancourses/tartil
sudo bash enable-django-ssl.sh
```

This enables:
- `SECURE_SSL_REDIRECT` - Redirects all HTTP to HTTPS
- `SESSION_COOKIE_SECURE` - Secure session cookies
- `CSRF_COOKIE_SECURE` - Secure CSRF cookies
- `SECURE_HSTS_SECONDS` - HTTP Strict Transport Security

## Step 4: Verify Everything

Check the following:

```bash
# Check certificate status
sudo certbot certificates

# Test auto-renewal
sudo certbot renew --dry-run

# Check Nginx status
sudo systemctl status nginx

# Check Django app status
sudo systemctl status tartil

# View Nginx error logs
sudo tail -f /var/log/nginx/tartil_error.log
```

## Manual Steps (if script fails)

If the automated script doesn't work, follow these manual steps:

### 1. Install Certbot

```bash
sudo apt-get update
sudo apt-get install -y certbot python3-certbot-nginx
```

### 2. Get Certificate

```bash
sudo certbot --nginx -d qurancourses.org -d www.qurancourses.org
```

### 3. Copy Nginx Config

```bash
sudo cp /home/hamzoooz123/qurancourses/tartil/nginx-ssl.conf /etc/nginx/sites-available/tartil
sudo nginx -t
sudo systemctl restart nginx
```

### 4. Update Django Settings

Edit `tartil/settings.py` and uncomment these lines:

```python
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

Then restart:

```bash
sudo systemctl restart tartil
```

## Certificate Renewal

Let's Encrypt certificates expire every 90 days. Auto-renewal is already configured, but you can manually test it:

```bash
sudo certbot renew --dry-run
```

## Troubleshooting

### Certificate not working?
- Check DNS is pointing to the correct IP: `dig qurancourses.org`
- Check port 443 is open: `sudo ufw status` or `sudo iptables -L`
- Check Nginx error logs: `sudo tail -f /var/log/nginx/error.log`

### Mixed content warnings?
- Make sure all resources use HTTPS
- Check browser console for HTTP resources
- Update any hardcoded HTTP URLs in templates

### Redirect loops?
- Check `SECURE_SSL_REDIRECT` in Django
- Check Nginx redirect configuration
- Make sure `X-Forwarded-Proto` header is set correctly

## Security Headers Enabled

After setup, these security headers are active:

- `X-Frame-Options: SAMEORIGIN`
- `X-Content-Type-Options: nosniff`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Strict-Transport-Security` (HSTS) - after confirmation

## Files Created/Modified

- `/etc/nginx/sites-available/tartil` - Nginx config
- `/etc/letsencrypt/live/qurancourses.org/` - SSL certificates
- `tartil/settings.py` - Django SSL settings
- `setup-ssl.sh` - SSL setup script
- `nginx-ssl.conf` - Nginx SSL configuration template
