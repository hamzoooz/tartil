"""
مهام النظام - Tasks for Notification System
"""
import logging
from django.utils import timezone

logger = logging.getLogger(__name__)


def send_scheduled_notification(notification_id: str, immediate: bool = False):
    """إرسال إشعار مجدول"""
    from .models import ScheduledNotification
    from .services import NotificationDispatchService
    
    try:
        notification = ScheduledNotification.objects.get(id=notification_id)
        
        if not immediate and notification.status != ScheduledNotification.Status.SCHEDULED:
            return {'status': 'skipped', 'reason': 'not_scheduled'}
        
        if not notification.is_enabled:
            return {'status': 'skipped', 'reason': 'disabled'}
        
        dispatch_service = NotificationDispatchService()
        results = dispatch_service.dispatch_notification(
            notification=notification,
            immediate=immediate
        )
        
        return {
            'status': 'completed',
            'notification_id': str(notification_id),
            'total': results['total'],
            'success': results['success'],
            'failed': results['failed'],
        }
        
    except ScheduledNotification.DoesNotExist:
        return {'status': 'error', 'reason': 'not_found'}
    except Exception as e:
        logger.exception(f"Error sending notification {notification_id}: {e}")
        return {'status': 'error', 'reason': str(e)}


def process_pending_notifications(batch_size: int = 50):
    """معالجة الإشعارات المعلقة"""
    from .services import SchedulingService
    
    try:
        pending = SchedulingService.get_pending_notifications(limit=batch_size)
        logger.info(f"Found {len(pending)} pending notifications")
        
        results = []
        for notification in pending:
            result = send_scheduled_notification(str(notification.id))
            results.append(result)
        
        successful = sum(1 for r in results if r['status'] == 'completed')
        
        return {
            'status': 'completed',
            'processed': len(pending),
            'successful': successful,
        }
        
    except Exception as e:
        logger.exception(f"Error processing pending notifications: {e}")
        return {'status': 'error', 'error': str(e)}


def retry_failed_notifications(notification_id: str = None):
    """إعادة محاولة الإشعارات الفاشلة"""
    from .services import NotificationDispatchService
    
    try:
        dispatch_service = NotificationDispatchService()
        
        if notification_id:
            from .models import ScheduledNotification
            notification = ScheduledNotification.objects.get(id=notification_id)
            results = dispatch_service.retry_failed_dispatches(notification)
        else:
            results = dispatch_service.retry_failed_dispatches()
        
        return {
            'status': 'completed',
            'retried': results['retried'],
            'success': results['success'],
            'failed': results['failed'],
        }
        
    except Exception as e:
        logger.exception(f"Error retrying failed notifications: {e}")
        return {'status': 'error', 'error': str(e)}


def generate_recurring_instances(parent_notification_id: str):
    """إنشاء نسخ متكررة"""
    from .models import ScheduledNotification
    from .services import SchedulingService
    
    try:
        parent = ScheduledNotification.objects.get(id=parent_notification_id)
        instances = SchedulingService.create_recurring_instances(parent)
        
        return {
            'status': 'completed',
            'parent_id': str(parent_notification_id),
            'instances_created': len(instances),
        }
        
    except ScheduledNotification.DoesNotExist:
        return {'status': 'error', 'reason': 'notification_not_found'}
    except Exception as e:
        logger.exception(f"Error generating recurring instances: {e}")
        return {'status': 'error', 'error': str(e)}


def cleanup_old_dispatch_logs(days: int = 90):
    """تنظيف السجلات القديمة"""
    from datetime import timedelta
    from .models import NotificationDispatchLog
    
    try:
        cutoff_date = timezone.now() - timedelta(days=days)
        
        deleted, _ = NotificationDispatchLog.objects.filter(
            status=NotificationDispatchLog.Status.SUCCESS,
            created_at__lt=cutoff_date
        ).delete()
        
        logger.info(f"Cleaned up {deleted} old dispatch logs")
        return {'status': 'completed', 'deleted': deleted}
        
    except Exception as e:
        logger.exception(f"Error cleaning up logs: {e}")
        return {'status': 'error', 'error': str(e)}
