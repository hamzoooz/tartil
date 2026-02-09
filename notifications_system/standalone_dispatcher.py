"""
موزع مستقل للإشعارات - للاستخدام بدون Celery
Standalone Dispatcher for Notifications (without Celery)
"""
import logging
import threading
from django.utils import timezone

from .services import SchedulingService, NotificationDispatchService

logger = logging.getLogger(__name__)


def run_pending_notifications_sync(batch_size=50):
    """تشغيل الإشعارات المعلقة بشكل متزامن"""
    try:
        pending = SchedulingService.get_pending_notifications(limit=batch_size)
        
        logger.info(f"Processing {len(pending)} pending notifications")
        
        dispatch_service = NotificationDispatchService()
        
        for notification in pending:
            try:
                dispatch_service.dispatch_notification(
                    notification=notification,
                    immediate=False
                )
            except Exception as e:
                logger.exception(f"Error dispatching notification {notification.id}: {e}")
        
        return len(pending)
        
    except Exception as e:
        logger.exception(f"Error in run_pending_notifications_sync: {e}")
        return 0


def run_in_background(func, *args, **kwargs):
    """تشغيل دالة في خلفية منفصلة"""
    thread = threading.Thread(target=func, args=args, kwargs=kwargs)
    thread.daemon = True
    thread.start()
    return thread
