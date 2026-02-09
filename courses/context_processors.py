"""
Context processors for Courses app
معالجات السياق للمقررات
"""
from django.utils import timezone
from datetime import date


def notifications_context(request):
    """إضافة الإشعارات غير المقروءة إلى السياق"""
    if not request.user.is_authenticated:
        return {'unread_notifications_count': 0}
    
    try:
        from accounts.models import Notification
        unread_count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()
        
        recent_notifications = Notification.objects.filter(
            user=request.user
        ).order_by('-created_at')[:5]
        
        return {
            'unread_notifications_count': unread_count,
            'recent_notifications': recent_notifications,
        }
    except:
        return {'unread_notifications_count': 0}


def courses_context(request):
    """إضافة بيانات المقررات إلى السياق"""
    if not request.user.is_authenticated or not request.user.is_student:
        return {}
    
    try:
        from .models import StudentCurriculum, LessonReminder
        
        # مقررات الطلب
        my_curriculums = StudentCurriculum.objects.filter(
            student=request.user,
            status__in=['not_started', 'in_progress']
        ).select_related('curriculum')[:3]
        
        # دروس اليوم
        today = date.today()
        today_lessons = LessonReminder.objects.filter(
            student_curriculum__student=request.user,
            scheduled_date=today,
            is_completed=False
        ).select_related('lesson', 'student_curriculum__curriculum')
        
        return {
            'my_curriculums': my_curriculums,
            'today_lessons_count': today_lessons.count(),
            'today_lessons': today_lessons[:5],
        }
    except:
        return {}
