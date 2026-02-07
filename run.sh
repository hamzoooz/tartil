#!/bin/bash
# Tartil Platform Startup Script

cd "$(dirname "$0")"

# Activate virtual environment
source venv/bin/activate

# Collect static files
python manage.py collectstatic --noinput

# Run migrations
python manage.py migrate --noinput

# Start Gunicorn
exec gunicorn tartil.wsgi:application -c gunicorn.conf.py
