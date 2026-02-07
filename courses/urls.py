"""
Courses URLs
مسارات المقررات والدروس
"""
from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    # المقررات
    path('', views.curriculum_list, name='list'),
    path('<int:pk>/', views.curriculum_detail, name='detail'),
    path('<int:pk>/enroll/', views.curriculum_enroll, name='enroll'),
    
    # دروس المقرر
    path('lesson/<int:pk>/', views.lesson_detail, name='lesson_detail'),
    path('lesson/<int:pk>/complete/', views.lesson_complete, name='lesson_complete'),
    
    # كلمات تحفيزية
    path('quotes/', views.quote_list, name='quotes'),
    path('quotes/<int:pk>/', views.quote_detail, name='quote_detail'),
    
    # تفسير
    path('tafseer/', views.tafseer_list, name='tafseer_list'),
    path('tafseer/<int:pk>/', views.tafseer_detail, name='tafseer_detail'),
    
    # الإشعارات
    path('notifications/', views.my_notifications, name='notifications'),
    path('notifications/<int:pk>/read/', views.mark_notification_read, name='mark_notification_read'),
    
    # API
    path('api/my-curriculums/', views.api_my_curriculums, name='api_my_curriculums'),
    path('api/today-lessons/', views.api_today_lessons, name='api_today_lessons'),
]