# Quran Courses Deployment Summary

## ✅ Deployment Status: COMPLETE (HTTP)

### Server Information
- **Server IP:** 34.18.216.179
- **Domain:** qurancourses.org / www.qurancourses.org
- **Project Path:** `/home/hamzoooz123/qurancourses/tartil`
- **Server User:** hamzoooz123

### Services Status
| Service | Status | Port |
|---------|--------|------|
| Gunicorn (Quran Courses) | ✅ Active | 127.0.0.1:8005 |
| Nginx | ✅ Active | 80 |

### What Was Deployed
1. ✅ Python 3.10 virtual environment
2. ✅ Django application with all dependencies
3. ✅ Database migrations applied
4. ✅ Static files collected
5. ✅ Gunicorn WSGI server
6. ✅ Nginx reverse proxy
7. ✅ Systemd service for auto-start

### Access the Site
- **Via IP:** http://34.18.216.179/
- **Via Domain:** http://qurancourses.org/ (after DNS setup)

---

## 🔐 SSL/HTTPS Setup (Next Step)

To enable HTTPS with SSL certificates, you need to:

### Step 1: Configure DNS
Point your domain to this server's IP address:

| Record Type | Host | Value |
|-------------|------|-------|
| A | @ | 34.18.216.179 |
| A | www | 34.18.216.179 |

### Step 2: Run SSL Setup Script
After DNS propagation (can take up to 24-48 hours), run:

```bash
cd /home/hamzoooz123/qurancourses/tartil
sudo bash deploy/setup-ssl.sh admin@qurancourses.org
```

Or manually:
```bash
# Install Certbot
sudo apt-get install -y certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d qurancourses.org -d www.qurancourses.org

# Restart services
sudo systemctl restart nginx
```

### Step 3: Re-enable Security Settings
After SSL is working, edit `tartil/settings.py` and re-enable security settings:

```python
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_SSL_REDIRECT = True        # Enable this
    SESSION_COOKIE_SECURE = True      # Enable this
    CSRF_COOKIE_SECURE = True         # Enable this
    SECURE_HSTS_SECONDS = 31536000    # Enable this
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
```

Then restart:
```bash
sudo systemctl restart tartil
```

---

## 🔧 Useful Commands

### Service Management
```bash
# Check status
sudo systemctl status tartil
sudo systemctl status nginx

# Restart services
sudo systemctl restart tartil
sudo systemctl restart nginx

# View logs
sudo journalctl -u tartil -f
sudo tail -f /var/log/nginx/tartil_error.log
```

### Django Management
```bash
cd /home/hamzoooz123/qurancourses/tartil
source venv/bin/activate

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Create superuser
python manage.py createsuperuser

# Django shell
python manage.py shell
```

### SSL Certificate
```bash
# Test certificate renewal
sudo certbot renew --dry-run

# Renew manually
sudo certbot renew

# View certificate info
sudo certbot certificates
```

---

## 📁 Important Files

| File | Description |
|------|-------------|
| `/home/hamzoooz123/qurancourses/tartil/.env` | Environment variables (SECRET_KEY, DEBUG) |
| `/home/hamzoooz123/qurancourses/tartil/tartil/settings.py` | Django settings |
| `/etc/nginx/sites-available/tartil` | Nginx configuration |
| `/etc/systemd/system/tartil.service` | Systemd service file |
| `/var/log/nginx/tartil_error.log` | Nginx error logs |
| `/var/log/gunicorn/` | Gunicorn logs |

---

## 🔒 Security Notes

1. **Change the default SECRET_KEY** in `/home/hamzoooz123/qurancourses/tartil/.env`
2. **Set DEBUG=False** in production (already set)
3. **Enable SSL/HTTPS** as soon as possible (follow steps above)
4. **Regular backups** of the SQLite database at `/home/hamzoooz123/qurancourses/tartil/db.sqlite3`

---

## 📞 Support

If you encounter any issues:
1. Check logs: `sudo journalctl -u tartil -f`
2. Verify Nginx config: `sudo nginx -t`
3. Check Gunicorn is listening: `sudo ss -tlnp | grep 8005`
