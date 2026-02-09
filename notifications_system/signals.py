"""
إشارات (Signals) لنظام النشر
Signals for Notification System
"""
import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.utils import timezone

from .models import ScheduledNotification, NotificationAuditLog

logger = logging.getLogger(__name__)


@receiver(post_save, sender=ScheduledNotification)
def log_notification_create(sender, instance, created, **kwargs):
    """تسجيل إنشاء/تحديث الإشعار"""
    if created:
        # لا نحتاج لتسجيل هنا لأنه يتم في الـ View
        pass


@receiver(pre_delete, sender=ScheduledNotification)
def log_notification_delete(sender, instance, **kwargs):
    """تسجيل حذف الإشعار"""
    logger.info(f"Notification {instance.id} is being deleted")
