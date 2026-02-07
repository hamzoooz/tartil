"""
Utilities for Notifications
أدوات مساعدة للإشعارات
"""
from django.urls import reverse
from django.utils import timezone


def create_notification(user, notification_type, title, message, link=''):
    """
    إنشاء إشعار جديد للمستخدم
    
    Args:
        user: المستخدم المستهدف
        notification_type: نوع الإشعار (session, grade, badge, system, reminder)
        title: عنوان الإشعار
        message: نص الإشعار
        link: رابط اختياري
    """
    from .models import Notification
    
    return Notification.objects.create(
        user=user,
        notification_type=notification_type,
        title=title,
        message=message,
        link=link
    )


def notify_recitation_recorded(recitation_record):
    """
    إشعار الطالب عند تسجيل تسميع جديد
    """
    student = recitation_record.student
    surah = recitation_record.surah_start.name_arabic
    grade = recitation_record.grade
    
    title = f"تم تسجيل تسميع جديد - {surah}"
    message = f"قام الشيخ بتسجيل تسميعك لسورة {surah} بدرجة {grade}/100"
    
    create_notification(
        user=student,
        notification_type='grade',
        title=title,
        message=message,
        link=reverse('recitation:my_records')
    )


def notify_attendance_recorded(attendance):
    """
    إشعار الطالب عند تسجيل الحضور
    """
    student = attendance.student
    session = attendance.session
    status_display = attendance.get_status_display()
    
    title = f"تسجيل {status_display}"
    message = f"تم تسجيل {status_display} في جلسة {session.halaqa.name} بتاريخ {session.date}"
    
    create_notification(
        user=student,
        notification_type='session',
        title=title,
        message=message,
        link=reverse('halaqat:my_halaqat')
    )


def notify_badge_earned(student_badge):
    """
    إشعار الطالب عند حصوله على وسام جديد
    """
    student = student_badge.student
    badge = student_badge.badge
    
    title = f"🎉 مبروك! حصلت على وسام {badge.name}"
    message = f"تهانينا! لقد حصلت على الوسام {badge.name} ({badge.get_level_display()})"
    
    create_notification(
        user=student,
        notification_type='badge',
        title=title,
        message=message,
        link=reverse('gamification:badges')
    )


def notify_points_added(points_log):
    """
    إشعار الطالب عند إضافة نقاط
    """
    student = points_log.student
    points = points_log.points
    
    if points > 0:
        title = f"✨ تم إضافة {points} نقطة"
        message = f"تم إضافة {points} نقطة إلى رصيدك. السبب: {points_log.reason}"
    else:
        title = f"⚠️ تم خصم {abs(points)} نقطة"
        message = f"تم خصم {abs(points)} نقطة من رصيدك. السبب: {points_log.reason}"
    
    create_notification(
        user=student,
        notification_type='grade',
        title=title,
        message=message,
        link=reverse('gamification:leaderboard')
    )


def notify_session_created(session, students=None):
    """
    إشعار الطلاب عند إنشاء جلسة جديدة
    """
    halaqa = session.halaqa
    
    if students is None:
        from halaqat.models import HalaqaEnrollment
        students = HalaqaEnrollment.objects.filter(
            halaqa=halaqa,
            status='active'
        ).values_list('student', flat=True)
    
    title = f"جلسة جديدة في {halaqa.name}"
    message = f"تم جدولة جلسة جديدة في {halaqa.name} بتاريخ {session.date} الساعة {session.start_time}"
    
    for student_id in students:
        from .models import CustomUser
        try:
            student = CustomUser.objects.get(pk=student_id)
            create_notification(
                user=student,
                notification_type='session',
                title=title,
                message=message,
                link=reverse('halaqat:my_halaqat')
            )
        except CustomUser.DoesNotExist:
            pass


def notify_certificate_issued(certificate):
    """
    إشعار الطالب عند إصدار شهادة جديدة
    """
    student = certificate.student
    
    title = "🎓 تم إصدار شهادة جديدة"
    message = f"تهانينا! تم إصدار شهادة {certificate.degree_title or 'جديدة'} لك."
    
    create_notification(
        user=student,
        notification_type='badge',
        title=title,
        message=message,
        link=reverse('reports:my_reports')
    )


def notify_achievement_unlocked(student_achievement):
    """
    إشعار الطالب عند إنجاز إنجاز جديد
    """
    student = student_achievement.student
    achievement = student_achievement.achievement
    
    title = f"🏆 إنجاز جديد: {achievement.name}"
    message = f"مبروك! لقد أكملت الإنجاز: {achievement.description}"
    
    create_notification(
        user=student,
        notification_type='badge',
        title=title,
        message=message,
        link=reverse('gamification:badges')
    )


def notify_new_halaqa_enrollment(enrollment):
    """
    إشعار الشيخ عند تسجيل طالب جديد في حلقته
    """
    sheikh = enrollment.halaqa.sheikh
    student = enrollment.student
    halaqa = enrollment.halaqa
    
    title = f"طالب جديد في {halaqa.name}"
    message = f"قام {student.get_full_name()} بالتسجيل في حلقة {halaqa.name}"
    
    create_notification(
        user=sheikh,
        notification_type='system',
        title=title,
        message=message,
        link=reverse('halaqat:manage')
    )


def notify_curriculum_completed(student_curriculum):
    """
    إشعار الطالب والشيخ عند إكمال مقرر
    """
    student = student_curriculum.student
    curriculum = student_curriculum.curriculum
    sheikh = student_curriculum.sheikh
    
    # إشعار الطالب
    title = f"📚 أكملت المقرر: {curriculum.name}"
    message = f"مبروك! لقد أكملت المقرر {curriculum.name} بنجاح."
    
    create_notification(
        user=student,
        notification_type='badge',
        title=title,
        message=message,
        link=reverse('courses:list')
    )
    
    # إشعار الشيخ
    if sheikh:
        title = f"طالب أكمل المقرر"
        message = f"قام {student.get_full_name()} بإكمال المقرر {curriculum.name}"
        
        create_notification(
            user=sheikh,
            notification_type='system',
            title=title,
            message=message,
            link=reverse('courses:list')
        )


def notify_memorization_progress_completed(progress):
    """
    إشعار عند إكمال حفظ سورة
    """
    student = progress.student
    surah = progress.surah
    
    title = f"📖 حفظت سورة {surah.name_arabic}"
    message = f"مبروك! لقد أكملت حفظ سورة {surah.name_arabic} بنجاح."
    
    create_notification(
        user=student,
        notification_type='badge',
        title=title,
        message=message,
        link=reverse('recitation:progress')
    )


def get_unread_notifications_count(user):
    """
    الحصول على عدد الإشعارات غير المقروءة
    """
    from .models import Notification
    return Notification.objects.filter(user=user, is_read=False).count()


def mark_all_notifications_as_read(user):
    """
    تحديد جميع إشعارات المستخدم كمقروءة
    """
    from .models import Notification
    return Notification.objects.filter(user=user, is_read=False).update(is_read=True)
