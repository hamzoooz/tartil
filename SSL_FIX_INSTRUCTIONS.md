# SSL Fix for qurancourses.org

## Problem
The server is returning the wrong SSL certificate (`abaqalanaqa.qa` instead of `qurancourses.org`).

## Solution

### Option 1: Run the Fix Script (Recommended)

```bash
cd /home/hamzoooz123/qurancourses/tartil
sudo bash fix-ssl.sh admin@qurancourses.org
```

### Option 2: Manual Steps

If the script doesn't work, run these commands manually:

#### Step 1: Get SSL Certificate for qurancourses.org

```bash
# Install certbot if needed
sudo apt-get update
sudo apt-get install -y certbot python3-certbot-nginx

# Get certificate
sudo certbot certonly --nginx -d qurancourses.org -d www.qurancourses.org
```

#### Step 2: Update Nginx Configuration

Create the file `/etc/nginx/sites-available/tartil` with this content:

```nginx
# HTTP - Redirect to HTTPS
server {
    listen 80;
    server_name qurancourses.org www.qurancourses.org;
    return 301 https://$host$request_uri;
}

# HTTPS Server
server {
    listen 443 ssl http2;
    server_name qurancourses.org www.qurancourses.org;
    
    client_max_body_size 50M;

    # SSL (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/qurancourses.org/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/qurancourses.org/privkey.pem;
    
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
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Port $server_port;
        proxy_redirect off;
        proxy_connect_timeout 300s;
        proxy_read_timeout 300s;
    }
}
```

#### Step 3: Test and Reload

```bash
# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

#### Step 4: Verify

```bash
# Check certificate
echo | openssl s_client -connect qurancourses.org:443 -servername qurancourses.org 2>/dev/null | openssl x509 -noout -subject

# Should show: subject=CN = qurancourses.org
```

## Testing

After running the fix, test these URLs in your browser:
- https://qurancourses.org
- https://www.qurancourses.org

You should see a green lock icon ✅ instead of the privacy error.

## Troubleshooting

### Certificate still shows wrong domain?
```bash
# Check which certificate is being served
echo | openssl s_client -connect qurancourses.org:443 2>/dev/null | openssl x509 -noout -text | grep "Subject:"

# Check Nginx is using the right config
sudo nginx -T | grep -E "(server_name|ssl_certificate)"
```

### Nginx test fails?
```bash
# Check for syntax errors
sudo nginx -t

# Check error logs
sudo tail -f /var/log/nginx/error.log
```

### Certificate renewal issues?
```bash
# Test auto-renewal
sudo certbot renew --dry-run

# Force renew
sudo certbot renew --force-renewal -d qurancourses.org
```
