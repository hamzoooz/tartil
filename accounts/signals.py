"""
Signals for automatic notifications
الإشارات لإنشاء الإشعارات التلقائية
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .utils import (
    notify_recitation_recorded,
    notify_attendance_recorded,
    notify_badge_earned,
    notify_points_added,
    notify_session_created,
    notify_certificate_issued,
    notify_achievement_unlocked,
    notify_new_halaqa_enrollment,
    notify_memorization_progress_completed,
)


@receiver(post_save, sender='recitation.RecitationRecord')
def on_recitation_saved(sender, instance, created, **kwargs):
    """
    إشعار عند تسجيل تسميع جديد
    """
    if created:
        notify_recitation_recorded(instance)


@receiver(post_save, sender='halaqat.Attendance')
def on_attendance_saved(sender, instance, created, **kwargs):
    """
    إشعار عند تسجيل الحضور
    """
    if created:
        notify_attendance_recorded(instance)


@receiver(post_save, sender='gamification.StudentBadge')
def on_badge_earned(sender, instance, created, **kwargs):
    """
    إشعار عند الحصول على وسام
    """
    if created:
        notify_badge_earned(instance)


@receiver(post_save, sender='gamification.PointsLog')
def on_points_added(sender, instance, created, **kwargs):
    """
    إشعار عند إضافة نقاط
    """
    if created:
        notify_points_added(instance)


@receiver(post_save, sender='halaqat.Session')
def on_session_created(sender, instance, created, **kwargs):
    """
    إشعار عند إنشاء جلسة جديدة
    """
    if created:
        notify_session_created(instance)


@receiver(post_save, sender='reports.Certificate')
def on_certificate_issued(sender, instance, created, **kwargs):
    """
    إشعار عند إصدار شهادة
    """
    if created:
        notify_certificate_issued(instance)


@receiver(post_save, sender='gamification.StudentAchievement')
def on_achievement_unlocked(sender, instance, created, **kwargs):
    """
    إشعار عند إنجاز إنجاز جديد
    """
    if created:
        notify_achievement_unlocked(instance)
    elif instance.is_completed and not kwargs.get('raw', False):
        # إذا تم تحديث الإنجاز إلى مكتمل
        notify_achievement_unlocked(instance)


@receiver(post_save, sender='halaqat.HalaqaEnrollment')
def on_halaqa_enrollment(sender, instance, created, **kwargs):
    """
    إشعار عند تسجيل طالب جديد في حلقة
    """
    if created:
        notify_new_halaqa_enrollment(instance)


@receiver(post_save, sender='recitation.MemorizationProgress')
def on_memorization_progress_saved(sender, instance, created, **kwargs):
    """
    إشعار عند إكمال حفظ سورة
    """
    if instance.is_memorized and not created:
        # التحقق مما إذا كان هذا تحديث للحفظ
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            if not old_instance.is_memorized:
                notify_memorization_progress_completed(instance)
        except sender.DoesNotExist:
            pass
    elif created and instance.is_memorized:
        notify_memorization_progress_completed(instance)
