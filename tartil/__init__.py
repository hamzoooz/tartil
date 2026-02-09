"""
Tartil Project - Quran Courses Platform
"""

# Try to import Celery, but don't fail if it's not installed
try:
    from .celery import app as celery_app
    __all__ = ('celery_app',)
except ImportError:
    # Celery not installed, use standalone mode
    celery_app = None
    __all__ = ()
