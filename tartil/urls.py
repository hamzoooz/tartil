"""
مسارات مشروع دورات القرآن
Quran Courses Project URLs
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# تخصيص لوحة الإدارة
admin.site.site_header = 'إدارة منصة دورات القرآن'
admin.site.site_title = 'دورات القرآن'
admin.site.index_title = 'لوحة التحكم'

urlpatterns = [
    # لوحة الإدارة المتقدمة (الجديدة)
    path('dashboard/', include('dashboard.urls', namespace='dashboard')),
    
    # لوحة الإدارة الافتراضية
    path('admin/', admin.site.urls),

    # التطبيقات
    path('', include('core.urls', namespace='core')),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('quran/', include('quran.urls', namespace='quran')),
    path('halaqat/', include('halaqat.urls', namespace='halaqat')),
    path('recitation/', include('recitation.urls', namespace='recitation')),
    path('gamification/', include('gamification.urls', namespace='gamification')),
    path('reports/', include('reports.urls', namespace='reports')),
    path('courses/', include('courses.urls', namespace='courses')),
    
    # نظام النشر والتنبيهات المجدول
    path('notifications-system/', include('notifications_system.urls', namespace='notifications_system')),
]

# خدمة ملفات الوسائط في وضع التطوير
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
