"""
Context Processors for Core App
معالجات السياق للتطبيق الأساسي
"""
from django.conf import settings


def site_settings(request):
    """
    Add site settings to all templates context
    إضافة إعدادات الموقع لسياق جميع القوالب
    """
    return {
        'SITE_NAME': getattr(settings, 'SITE_NAME', 'إدارة الدورات القرآنية'),
        'SITE_LOGO': getattr(settings, 'SITE_LOGO', 'images/logo3.png'),
        'SITE_LOGO_SMALL': getattr(settings, 'SITE_LOGO_SMALL', 'images/logo.jpeg'),
        'SITE_TAGLINE': getattr(settings, 'SITE_TAGLINE', 'منصة إدارة الحلقات القرآنية الذكية'),
    }
