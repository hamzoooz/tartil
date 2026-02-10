"""
إعدادات مشروع دورات القرآن
Django settings for Quran Courses project.
"""

from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-v39qy$k1y=815g+yf$7d1my(j23i-9&&7j4gge@n-9=8399j-l')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'

ALLOWED_HOSTS = ['tartil.zolna.app', 'www.tartil.zolna.app', 
                 'qurancourses.org', 'www.qurancourses.org',
                 'localhost', '127.0.0.1',
                 '34.18.216.179']

CSRF_TRUSTED_ORIGINS = ['https://tartil.zolna.app', 'https://www.tartil.zolna.app',
                         'https://qurancourses.org', 'https://www.qurancourses.org',
                         'http://localhost', 'http://127.0.0.1']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    # التطبيقات المحلية
    'accounts.apps.AccountsConfig',
    'core.apps.CoreConfig',
    'quran.apps.QuranConfig',
    'halaqat.apps.HalaqatConfig',
    'recitation.apps.RecitationConfig',
    'gamification.apps.GamificationConfig',
    'reports.apps.ReportsConfig',
    'courses.apps.CoursesConfig',
    # لوحة التحكم المتقدمة
    'dashboard.apps.DashboardConfig',
    # نظام النشر والتنبيهات المجدول
    'notifications_system.apps.NotificationsSystemConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'tartil.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                # معالجات السياق المخصصة
                'courses.context_processors.notifications_context',
                'courses.context_processors.courses_context',
                'dashboard.context_processors.dashboard_notifications',
                'core.context_processors.site_settings',
            ],
        },
    },
]

WSGI_APPLICATION = 'tartil.wsgi.application'

# Database - SQLite
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        'OPTIONS': {
            'timeout': 20,
        }
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization - Arabic
LANGUAGE_CODE = 'ar'
TIME_ZONE = 'Asia/Riyadh'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# اللغات المدعومة
LANGUAGES = [
    ('ar', 'العربية'),
    ('en', 'English'),
]

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = 'accounts.CustomUser'

# Login/Logout URLs
LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'core:dashboard'
LOGOUT_REDIRECT_URL = 'core:home'

# Messages
from django.contrib.messages import constants as messages
MESSAGE_TAGS = {
    messages.DEBUG: 'secondary',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'danger',
}

# Session settings
SESSION_COOKIE_AGE = 86400 * 7  # 7 days
SESSION_SAVE_EVERY_REQUEST = True

# WhiteNoise for static files
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# تفعيل WhiteNoise في جميع البيئات
WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = DEBUG

# Security settings for production
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    # SECURE_SSL_REDIRECT = True  # Temporarily disabled until SSL is set up
    # SESSION_COOKIE_SECURE = True
    # CSRF_COOKIE_SECURE = True
    # SECURE_HSTS_SECONDS = 31536000
    # SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    # SECURE_HSTS_PRELOAD = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
else:
    # إعدادات التطوير
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False

# إعدادات التخزين المؤقت
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# إعدادات الملفات المرفوعة
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5 MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5 MB

# CORS settings
CORS_ALLOW_ALL_ORIGINS = DEBUG

# Celery Configuration
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_ENABLE_UTC = True

# Celery Beat Schedule
CELERY_BEAT_SCHEDULE = {
    'process-scheduled-notifications': {
        'task': 'notifications_system.tasks.process_pending_notifications',
        'schedule': 60.0,  # كل دقيقة
        'args': (50,),  # دفعة من 50 إشعار
    },
    'retry-failed-notifications': {
        'task': 'notifications_system.tasks.retry_failed_notifications',
        'schedule': 300.0,  # كل 5 دقائق
    },
    'cleanup-old-logs': {
        'task': 'notifications_system.tasks.cleanup_old_dispatch_logs',
        'schedule': 86400.0,  # مرة يومياً
        'args': (90,),  # حذف سجلات أقدم من 90 يوم
    },
}

# Notification System Settings
NOTIFICATIONS_SETTINGS = {
    'DEFAULT_WEBHOOK_TIMEOUT': 30,
    'MAX_RETRY_ATTEMPTS': 3,
    'RETRY_DELAY_SECONDS': [5, 15, 30],
    'BATCH_SIZE': 50,
    'CLEANUP_OLDER_THAN_DAYS': 90,
}

# Site Settings
SITE_NAME = 'إدارة الدورات القرآنية'
SITE_LOGO = 'images/logo3_final.png'
SITE_LOGO_SMALL = 'images/logo_navbar.png'
SITE_TAGLINE = 'منصة إدارة الحلقات القرآنية الذكية'
