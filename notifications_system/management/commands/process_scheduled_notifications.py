"""
أمر إدارة: معالجة الإشعارات المجدولة
Management Command: Process Scheduled Notifications
"""
import logging
from django.core.management.base import BaseCommand
from notifications_system.tasks import process_pending_notifications

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'معالجة الإشعارات المجدولة المستحقة للإرسال'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=50,
            help='عدد الإشعارات لمعالجتها في كل دفعة (افتراضي: 50)'
        )
    
    def handle(self, *args, **options):
        batch_size = options['batch_size']
        
        self.stdout.write(
            self.style.NOTICE(f'جاري معالجة الإشعارات المجدولة (دفعة: {batch_size})...')
        )
        
        result = process_pending_notifications(batch_size)
        
        if result['status'] == 'completed':
            self.stdout.write(
                self.style.SUCCESS(
                    f'تم معالجة {result["processed"]} إشعار | '
                    f'نجح: {result.get("successful", 0)}'
                )
            )
        else:
            self.stdout.write(
                self.style.ERROR(f'خطأ: {result.get("error", "unknown error")}')
            )
