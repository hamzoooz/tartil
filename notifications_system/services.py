"""
طبقة الخدمات لنظام النشر والتنبيهات
Service Layer for Notification System
"""
import logging
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dateutil import rrule
from django.utils import timezone
from django.db import transaction

from .models import (
    ScheduledNotification,
    NotificationDispatchLog,
    WebhookEndpoint,
)

logger = logging.getLogger(__name__)


class PayloadBuilder:
    """يبني حمولة JSON للإرسال إلى Webhook"""
    
    @classmethod
    def build_payload(cls, notification, recipient, lesson=None, tafseer=None) -> Dict[str, Any]:
        """بناء حمولة البيانات الكاملة"""
        return {
            "type": notification.content_type,
            "title": notification.title,
            "message": cls._format_message(notification.message, recipient),
            "lesson": cls._build_lesson_data(lesson, tafseer),
            "target": cls._build_target_data(notification, recipient),
            "media": cls._build_media_data(notification),
            "metadata": {
                "notification_id": str(notification.id),
                "scheduled_at": notification.scheduled_datetime.isoformat() if notification.scheduled_datetime else None,
                "sent_at": timezone.now().isoformat(),
                "timezone": notification.timezone,
            },
            "recipient": {
                "id": recipient.id,
                "name": recipient.get_full_name(),
                "email": recipient.email,
                "role": recipient.user_type,
            }
        }
    
    @classmethod
    def _format_message(cls, message: str, recipient) -> str:
        """تنسيق الرسالة باستبدال المتغيرات"""
        if not message:
            return ""
        replacements = {
            '{student_name}': recipient.get_full_name() or '',
            '{first_name}': recipient.first_name or '',
            '{username}': recipient.username or '',
        }
        for key, value in replacements.items():
            message = message.replace(key, value)
        return message
    
    @classmethod
    def _build_lesson_data(cls, lesson=None, tafseer=None) -> Optional[Dict[str, Any]]:
        """بناء بيانات الدرس"""
        if tafseer:
            return {
                "id": str(tafseer.id),
                "title": tafseer.title,
                "content": tafseer.content,
                "summary": tafseer.summary,
                "surah": tafseer.surah.name_arabic if tafseer.surah else None,
                "ayah_from": tafseer.ayah_from,
                "ayah_to": tafseer.ayah_to,
                "video_url": tafseer.video_url,
                "audio_url": tafseer.audio_url,
                "pdf_url": tafseer.pdf_file.url if tafseer.pdf_file else None,
            }
        if lesson:
            return {
                "id": str(lesson.id),
                "title": lesson.title,
                "content": lesson.description,
                "surah": lesson.surah_from.name_arabic if lesson.surah_from else None,
                "ayah_from": lesson.ayah_from,
                "ayah_to": lesson.ayah_to,
                "lesson_type": lesson.lesson_type,
                "duration_minutes": lesson.duration_minutes,
            }
        return None
    
    @classmethod
    def _build_target_data(cls, notification, recipient) -> Dict[str, Any]:
        """بناء بيانات المستهدفين"""
        data = {
            "role": recipient.user_type,
            "target_type": notification.target_type,
        }
        if notification.target_halaqa:
            data.update({
                "halaqa_id": str(notification.target_halaqa.id),
                "halaqa_name": notification.target_halaqa.name,
            })
        if notification.target_course:
            data.update({
                "course_id": str(notification.target_course.id),
                "course_name": notification.target_course.name,
            })
        return data
    
    @classmethod
    def _build_media_data(cls, notification) -> Optional[Dict[str, Any]]:
        """بناء بيانات الوسائط"""
        data = {}
        if notification.image:
            data['image_url'] = notification.image.url
        if notification.link:
            data['link'] = notification.link
        return data if data else None


class NotificationDispatchService:
    """خدمة إرسال الإشعارات إلى Webhook"""
    
    DEFAULT_TIMEOUT = 30
    MAX_RETRIES = 3
    RETRY_DELAYS = [5, 15, 30]
    
    def __init__(self):
        self.payload_builder = PayloadBuilder()
    
    def dispatch_notification(self, notification: ScheduledNotification, immediate: bool = False) -> Dict[str, Any]:
        """إرسال إشعار إلى جميع المستلمين"""
        results = {'total': 0, 'success': 0, 'failed': 0, 'logs': []}
        
        if not immediate and notification.status != ScheduledNotification.Status.SCHEDULED:
            logger.warning(f"Notification {notification.id} is not scheduled for sending")
            return results
        
        if not notification.is_enabled:
            logger.warning(f"Notification {notification.id} is disabled")
            return results
        
        recipients = self._get_recipients(notification)
        results['total'] = len(recipients)
        
        if not recipients:
            logger.warning(f"No recipients found for notification {notification.id}")
            return results
        
        endpoints = WebhookEndpoint.objects.filter(is_active=True)
        if not endpoints:
            logger.error("No active webhook endpoints found")
            return results
        
        notification.status = ScheduledNotification.Status.SENDING
        notification.save(update_fields=['status'])
        
        for recipient in recipients:
            try:
                log = self._send_to_recipient(notification, recipient, endpoints)
                if log.status == NotificationDispatchLog.Status.SUCCESS:
                    results['success'] += 1
                else:
                    results['failed'] += 1
                results['logs'].append(log)
            except Exception as e:
                logger.exception(f"Error dispatching to {recipient}: {e}")
                results['failed'] += 1
        
        notification.successful_sends = results['success']
        notification.failed_sends = results['failed']
        notification.total_recipients = results['total']
        
        if results['failed'] == 0 and results['success'] > 0:
            notification.status = ScheduledNotification.Status.SENT
            notification.sent_at = timezone.now()
        elif results['success'] > 0:
            notification.status = ScheduledNotification.Status.SENT
            notification.sent_at = timezone.now()
        else:
            notification.status = ScheduledNotification.Status.FAILED
        
        notification.save()
        return results
    
    def _get_recipients(self, notification: ScheduledNotification) -> List[Any]:
        """الحصول على قائمة المستلمين"""
        from accounts.models import CustomUser
        
        target_type = notification.target_type
        
        if target_type == ScheduledNotification.TargetType.ALL_STUDENTS:
            return list(CustomUser.objects.filter(user_type='student', is_active=True))
        elif target_type == ScheduledNotification.TargetType.ALL_PARENTS:
            return list(CustomUser.objects.filter(user_type='parent', is_active=True))
        elif target_type == ScheduledNotification.TargetType.ALL_TEACHERS:
            return list(CustomUser.objects.filter(user_type='sheikh', is_active=True))
        elif target_type == ScheduledNotification.TargetType.HALAQA and notification.target_halaqa:
            enrollments = notification.target_halaqa.enrollments.filter(status='active').select_related('student')
            return [e.student for e in enrollments]
        elif target_type == ScheduledNotification.TargetType.COURSE and notification.target_course:
            enrollments = notification.target_course.enrolled_students.filter(status='active').select_related('student')
            return [e.student for e in enrollments]
        elif target_type == ScheduledNotification.TargetType.SPECIFIC_USERS:
            return list(notification.target_users.filter(is_active=True))
        return []
    
    def _send_to_recipient(self, notification, recipient, endpoints):
        """إرسال إشعار لمستلم محدد"""
        payload = self.payload_builder.build_payload(
            notification=notification,
            recipient=recipient,
            lesson=notification.lesson,
            tafseer=notification.tafseer
        )
        endpoint = endpoints.first()
        
        with transaction.atomic():
            log, created = NotificationDispatchLog.objects.get_or_create(
                notification=notification,
                recipient=recipient,
                webhook_url=endpoint.url,
                defaults={'payload': payload, 'status': NotificationDispatchLog.Status.PENDING}
            )
        
        return self._execute_send_with_retry(log, endpoint, payload)
    
    def _execute_send_with_retry(self, log, endpoint, payload):
        """تنفيذ الإرسال مع آلية إعادة المحاولة"""
        log.first_attempt_at = log.first_attempt_at or timezone.now()
        
        while log.attempt_count < log.max_attempts:
            log.attempt_count += 1
            log.last_attempt_at = timezone.now()
            
            try:
                response = self._make_http_request(
                    url=endpoint.url,
                    payload=payload,
                    timeout=endpoint.timeout_seconds or self.DEFAULT_TIMEOUT,
                    headers=endpoint.headers
                )
                
                log.response_status_code = response.status_code
                log.response_body = response.text[:1000]
                
                if response.status_code == 200:
                    log.status = NotificationDispatchLog.Status.SUCCESS
                    log.completed_at = timezone.now()
                    endpoint.success_count += 1
                    endpoint.last_used_at = timezone.now()
                    endpoint.save(update_fields=['success_count', 'last_used_at'])
                    log.save()
                    return log
                else:
                    log.error_message = f"HTTP {response.status_code}: {response.text[:500]}"
                    
            except requests.exceptions.Timeout:
                log.error_message = f"Request timeout"
            except requests.exceptions.ConnectionError:
                log.error_message = "Connection error"
            except Exception as e:
                log.error_message = f"Exception: {str(e)[:500]}"
            
            if log.attempt_count < log.max_attempts:
                log.status = NotificationDispatchLog.Status.RETRYING
                log.save()
                import time
                delay = self.RETRY_DELAYS[min(log.attempt_count - 1, len(self.RETRY_DELAYS) - 1)]
                time.sleep(delay)
            else:
                log.status = NotificationDispatchLog.Status.FAILED
                log.completed_at = timezone.now()
                endpoint.failure_count += 1
                endpoint.last_used_at = timezone.now()
                endpoint.save(update_fields=['failure_count', 'last_used_at'])
                log.save()
        
        return log
    
    def _make_http_request(self, url: str, payload: Dict[str, Any], timeout: int, headers: Dict[str, str]):
        """إجراء طلب HTTP POST"""
        default_headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Source': 'quran-courses-platform',
        }
        default_headers.update(headers)
        return requests.post(url=url, json=payload, headers=default_headers, timeout=timeout)
    
    def retry_failed_dispatches(self, notification: ScheduledNotification = None):
        """إعادة محاولة الإرسالات الفاشلة"""
        logs = NotificationDispatchLog.objects.filter(
            status=NotificationDispatchLog.Status.FAILED,
            attempt_count__lt=models.F('max_attempts')
        )
        if notification:
            logs = logs.filter(notification=notification)
        
        results = {'retried': 0, 'success': 0, 'failed': 0}
        for log in logs:
            try:
                endpoint = WebhookEndpoint.objects.filter(is_active=True, url=log.webhook_url).first()
                if endpoint:
                    self._execute_send_with_retry(log, endpoint, log.payload)
                    results['retried'] += 1
                    if log.status == NotificationDispatchLog.Status.SUCCESS:
                        results['success'] += 1
                    else:
                        results['failed'] += 1
            except Exception as e:
                logger.exception(f"Error retrying log {log.id}: {e}")
                results['failed'] += 1
        return results


class SchedulingService:
    """خدمة إدارة جدولة الإشعارات"""
    
    @classmethod
    def create_recurring_instances(cls, parent_notification: ScheduledNotification) -> List[ScheduledNotification]:
        """إنشاء نسخ متكررة من الإشعار"""
        if parent_notification.recurrence_type == ScheduledNotification.RecurrenceType.ONE_TIME:
            return []
        
        instances = []
        base_datetime = parent_notification.scheduled_datetime
        end_date = parent_notification.recurrence_end_date
        
        if not end_date:
            end_date = (base_datetime + timedelta(days=90)).date()
        
        occurrence_dates = cls._calculate_occurrences(
            start_date=base_datetime,
            end_date=end_date,
            recurrence_type=parent_notification.recurrence_type,
            recurrence_days=parent_notification.recurrence_days
        )
        
        for occ_datetime in occurrence_dates[1:]:
            try:
                instance = cls._create_instance(parent=parent_notification, scheduled_datetime=occ_datetime)
                instances.append(instance)
            except Exception as e:
                logger.exception(f"Error creating instance for {occ_datetime}: {e}")
        
        return instances
    
    @classmethod
    def _calculate_occurrences(cls, start_date: datetime, end_date, recurrence_type: str, recurrence_days: List[int]):
        """حساب مواعيد التكرار"""
        end_datetime = datetime.combine(end_date, start_date.time())
        end_datetime = end_datetime.replace(tzinfo=start_date.tzinfo)
        
        if recurrence_type == ScheduledNotification.RecurrenceType.DAILY:
            return list(rrule.rrule(rrule.DAILY, dtstart=start_date, until=end_datetime))
        elif recurrence_type == ScheduledNotification.RecurrenceType.WEEKLY:
            return list(rrule.rrule(rrule.WEEKLY, dtstart=start_date, until=end_datetime))
        elif recurrence_type == ScheduledNotification.RecurrenceType.BIWEEKLY:
            if recurrence_days:
                occurrences = []
                current = start_date
                while current <= end_datetime:
                    if current.weekday() in recurrence_days:
                        occurrences.append(current)
                    current += timedelta(days=1)
                return occurrences
            else:
                return list(rrule.rrule(rrule.WEEKLY, byweekday=[rrule.SU, rrule.TH], dtstart=start_date, until=end_datetime))
        elif recurrence_type == ScheduledNotification.RecurrenceType.MONTHLY:
            return list(rrule.rrule(rrule.MONTHLY, dtstart=start_date, until=end_datetime))
        elif recurrence_type == ScheduledNotification.RecurrenceType.CUSTOM:
            if recurrence_days:
                occurrences = []
                current = start_date
                while current <= end_datetime:
                    if current.weekday() in recurrence_days:
                        occurrences.append(current)
                    current += timedelta(days=1)
                return occurrences
        return [start_date]
    
    @classmethod
    def _create_instance(cls, parent: ScheduledNotification, scheduled_datetime: datetime) -> ScheduledNotification:
        """إنشاء نسخة فرعية من الإشعار"""
        instance = ScheduledNotification.objects.create(
            title=parent.title,
            content_type=parent.content_type,
            template=parent.template,
            message=parent.message,
            image=parent.image,
            link=parent.link,
            lesson=parent.lesson,
            tafseer=parent.tafseer,
            scheduled_datetime=scheduled_datetime,
            timezone=parent.timezone,
            recurrence_type=ScheduledNotification.RecurrenceType.ONE_TIME,
            target_type=parent.target_type,
            target_halaqa=parent.target_halaqa,
            target_course=parent.target_course,
            status=ScheduledNotification.Status.SCHEDULED,
            is_enabled=parent.is_enabled,
            parent_notification=parent,
            created_by=parent.created_by,
        )
        if parent.target_type == ScheduledNotification.TargetType.SPECIFIC_USERS:
            instance.target_users.set(parent.target_users.all())
        return instance
    
    @classmethod
    def get_pending_notifications(cls, limit: int = 100) -> List[ScheduledNotification]:
        """الحصول على الإشعارات المستحقة للإرسال"""
        now = timezone.now()
        return list(ScheduledNotification.objects.filter(
            status=ScheduledNotification.Status.SCHEDULED,
            is_enabled=True,
            scheduled_datetime__lte=now
        ).order_by('scheduled_datetime')[:limit])
    
    @classmethod
    def cancel_notification(cls, notification: ScheduledNotification, user=None, cancel_children: bool = True) -> bool:
        """إلغاء إشعار"""
        from .models import NotificationAuditLog
        
        if notification.status in [ScheduledNotification.Status.SENT, ScheduledNotification.Status.CANCELLED]:
            return False
        
        notification.status = ScheduledNotification.Status.CANCELLED
        notification.is_enabled = False
        notification.save()
        
        NotificationAuditLog.objects.create(
            notification=notification,
            user=user,
            action=NotificationAuditLog.ActionType.CANCELLED
        )
        
        if cancel_children:
            notification.child_notifications.filter(
                status__in=[ScheduledNotification.Status.SCHEDULED, ScheduledNotification.Status.DRAFT]
            ).update(status=ScheduledNotification.Status.CANCELLED, is_enabled=False)
        
        return True
    
    @classmethod
    def duplicate_notification(cls, notification: ScheduledNotification, user=None):
        """تكرار إشعار"""
        new_notification = ScheduledNotification.objects.create(
            title=f"{notification.title} (نسخة)",
            content_type=notification.content_type,
            template=notification.template,
            message=notification.message,
            image=notification.image,
            link=notification.link,
            lesson=notification.lesson,
            tafseer=notification.tafseer,
            scheduled_datetime=notification.scheduled_datetime,
            timezone=notification.timezone,
            recurrence_type=ScheduledNotification.RecurrenceType.ONE_TIME,
            target_type=notification.target_type,
            target_halaqa=notification.target_halaqa,
            target_course=notification.target_course,
            status=ScheduledNotification.Status.DRAFT,
            is_enabled=False,
            created_by=user or notification.created_by,
        )
        if notification.target_type == ScheduledNotification.TargetType.SPECIFIC_USERS:
            new_notification.target_users.set(notification.target_users.all())
        return new_notification


# Import models here to avoid circular import
from django.db import models
