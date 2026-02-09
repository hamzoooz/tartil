"""
أمر إدارة: إعادة محاولة الإشعارات الفاشلة
Management Command: Retry Failed Notifications
"""
import logging
from django.core.management.base import BaseCommand
from notifications_system.tasks import retry_failed_notifications

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'إعادة محاولة إرسال الإشعارات الفاشلة'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--notification-id',
            type=str,
            help='معرف إشعار محدد لإعادة المحاولة (اختياري)'
        )
    
    def handle(self, *args, **options):
        notification_id = options.get('notification_id')
        
        if notification_id:
            self.stdout.write(
                self.style.NOTICE(f'جاري إعادة المحاولة للإشعار: {notification_id}')
            )
        else:
            self.stdout.write(
                self.style.NOTICE('جاري إعادة المحاولة لجميع الإشعارات الفاشلة...')
            )
        
        result = retry_failed_notifications(notification_id)
        
        if result['status'] == 'completed':
            self.stdout.write(
                self.style.SUCCESS(
                    f'تمت إعادة المحاولة: {result["retried"]} | '
                    f'نجح: {result["success"]} | '
                    f'فشل: {result["failed"]}'
                )
            )
        else:
            self.stdout.write(
                self.style.ERROR(f'خطأ: {result.get("error", "unknown error")}')
            )
