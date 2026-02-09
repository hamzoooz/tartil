"""
Core Views
الصفحات الأساسية
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg, Sum
from django.utils import timezone
from datetime import timedelta


def home(request):
    """الصفحة الرئيسية"""
    return render(request, 'core/home.html')


def about(request):
    """عن المنصة"""
    return render(request, 'core/about.html')


def contact(request):
    """تواصل معنا"""
    if request.method == 'POST':
        # Handle contact form submission
        pass
    return render(request, 'core/contact.html')


@login_required
def dashboard(request):
    """لوحة التحكم"""
    user = request.user
    context = {}

    if user.is_student:
        # بيانات الطالب
        try:
            profile = user.student_profile
            context.update({
                'total_memorized_pages': profile.total_memorized_pages,
                'total_points': profile.total_points,
                'memorization_percentage': profile.memorization_percentage,
                'current_surah': profile.current_surah,
                'current_ayah': profile.current_ayah,
            })
        except:
            pass

        # الجلسات
        context['total_sessions'] = user.recitation_records.count()

        # المواظبة
        try:
            streak = user.streak
            context['current_streak'] = streak.current_streak
        except:
            context['current_streak'] = 0

        # جلسة اليوم
        from halaqat.models import Session, HalaqaEnrollment
        today = timezone.now().date()
        enrollments = HalaqaEnrollment.objects.filter(student=user, status='active')
        halaqat_ids = enrollments.values_list('halaqa_id', flat=True)
        context['today_session'] = Session.objects.filter(
            halaqa_id__in=halaqat_ids,
            date=today,
            status='scheduled'
        ).first()

    elif user.is_sheikh:
        # بيانات الشيخ
        from halaqat.models import Halaqa, Session, HalaqaEnrollment
        halaqat = Halaqa.objects.filter(sheikh=user)
        context['total_halaqat'] = halaqat.count()
        context['total_students'] = HalaqaEnrollment.objects.filter(
            halaqa__in=halaqat, status='active'
        ).count()

        # جلسات هذا الأسبوع
        week_start = timezone.now().date() - timedelta(days=7)
        context['sessions_this_week'] = Session.objects.filter(
            halaqa__in=halaqat,
            date__gte=week_start
        ).count()

        try:
            context['average_rating'] = user.sheikh_profile.rating
        except:
            context['average_rating'] = 0

    elif user.is_admin:
        # بيانات الإدارة
        from accounts.models import CustomUser
        from halaqat.models import Halaqa, Session

        context['total_students'] = CustomUser.objects.filter(user_type='student').count()
        context['total_sheikhs'] = CustomUser.objects.filter(user_type='sheikh').count()
        context['total_halaqat'] = Halaqa.objects.count()
        context['sessions_today'] = Session.objects.filter(
            date=timezone.now().date()
        ).count()

    # الإشعارات الأخيرة
    context['notifications'] = user.notifications.filter(is_read=False)[:5]

    # النشاطات الأخيرة
    context['recent_activities'] = user.activities.all()[:10]

    return render(request, 'core/dashboard.html', context)
