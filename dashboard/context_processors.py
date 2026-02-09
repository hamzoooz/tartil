"""
معالجات السياق للداشبورد
"""
from .models import Message, Notification


def dashboard_notifications(request):
    """إضافة عدادات الإشعارات والرسائل للسياق"""
    if not request.user.is_authenticated:
        return {}
    
    # عدد الرسائل غير المقروءة
    unread_messages = Message.objects.filter(
        recipients=request.user,
        is_archived=False
    ).exclude(read_by=request.user).count()
    
    # عدد الإشعارات غير المقروءة
    unread_notifications = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).count()
    
    return {
        'unread_messages_count': unread_messages if unread_messages > 0 else '',
        'unread_notifications_count': unread_notifications if unread_notifications > 0 else '',
    }
