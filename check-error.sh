#!/bin/bash
# Check Django errors

cd /home/hamzoooz123/qurancourses/tartil
source venv/bin/activate

export DJANGO_SETTINGS_MODULE=tartil.settings

# Run Django check
python manage.py check 2>&1

# Show recent migrations
python manage.py showmigrations --list 2>&1 | head -20

# Try to access the shell
python -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tartil.settings')
import django
django.setup()
from django.conf import settings
print('DEBUG:', settings.DEBUG)
print('ALLOWED_HOSTS:', settings.ALLOWED_HOSTS)
"
