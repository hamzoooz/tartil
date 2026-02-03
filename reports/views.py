"""
Reports Views
صفحات التقارير
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg, Sum
from django.utils import timezone
from datetime import timedelta


@login_required
def admin_reports(request):
    """تقارير الإدارة"""
    if not request.user.is_admin:
        from django.shortcuts import redirect
        from django.contrib import messages
        messages.error(request, 'هذه الصفحة للإدارة فقط')
        return redirect('core:dashboard')

    from accounts.models import CustomUser
    from halaqat.models import Halaqa, Session
    from recitation.models import RecitationRecord

    # إحصائيات عامة
    stats = {
        'total_students': CustomUser.objects.filter(user_type='student').count(),
        'total_sheikhs': CustomUser.objects.filter(user_type='sheikh').count(),
        'total_halaqat': Halaqa.objects.count(),
        'active_halaqat': Halaqa.objects.filter(status='active').count(),
    }

    # إحصائيات الأسبوع
    week_start = timezone.now().date() - timedelta(days=7)
    stats['sessions_this_week'] = Session.objects.filter(date__gte=week_start).count()
    stats['recitations_this_week'] = RecitationRecord.objects.filter(
        created_at__date__gte=week_start
    ).count()

    # أفضل الطلاب
    from accounts.models import StudentProfile
    top_students = StudentProfile.objects.select_related('user').order_by(
        '-total_points'
    )[:10]

    # أكثر المشايخ نشاطاً
    active_sheikhs = CustomUser.objects.filter(
        user_type='sheikh'
    ).annotate(
        sessions_count=Count('taught_halaqat__sessions')
    ).order_by('-sessions_count')[:10]

    context = {
        'stats': stats,
        'top_students': top_students,
        'active_sheikhs': active_sheikhs,
    }
    return render(request, 'reports/admin.html', context)


@login_required
def sheikh_reports(request):
    """تقارير الشيخ"""
    if not request.user.is_sheikh:
        from django.shortcuts import redirect
        from django.contrib import messages
        messages.error(request, 'هذه الصفحة للمشايخ فقط')
        return redirect('core:dashboard')

    from halaqat.models import Halaqa, Session, HalaqaEnrollment
    from recitation.models import RecitationRecord

    halaqat = Halaqa.objects.filter(sheikh=request.user)

    # إحصائيات
    stats = {
        'total_halaqat': halaqat.count(),
        'total_students': HalaqaEnrollment.objects.filter(
            halaqa__in=halaqat, status='active'
        ).count(),
        'total_sessions': Session.objects.filter(halaqa__in=halaqat).count(),
    }

    # جلسات الأسبوع
    week_start = timezone.now().date() - timedelta(days=7)
    recent_sessions = Session.objects.filter(
        halaqa__in=halaqat,
        date__gte=week_start
    ).order_by('-date')

    # متوسط درجات الطلاب
    recent_records = RecitationRecord.objects.filter(
        session__halaqa__in=halaqat
    ).order_by('-created_at')[:20]

    context = {
        'stats': stats,
        'halaqat': halaqat,
        'recent_sessions': recent_sessions,
        'recent_records': recent_records,
    }
    return render(request, 'reports/sheikh.html', context)


@login_required
def student_report(request, student_id=None):
    """تقرير الطالب"""
    from accounts.models import CustomUser
    from recitation.models import RecitationRecord, MemorizationProgress

    if student_id:
        student = CustomUser.objects.get(pk=student_id)
        # التحقق من الصلاحية
        if not (request.user.is_admin or request.user.is_sheikh or request.user == student):
            from django.shortcuts import redirect
            from django.contrib import messages
            messages.error(request, 'غير مصرح لك بعرض هذا التقرير')
            return redirect('core:dashboard')
    else:
        student = request.user

    # سجلات التسميع
    records = RecitationRecord.objects.filter(student=student).order_by('-created_at')

    # تقدم الحفظ
    progress = MemorizationProgress.objects.filter(student=student)

    # إحصائيات
    stats = {
        'total_records': records.count(),
        'average_grade': records.aggregate(avg=Avg('grade'))['avg'] or 0,
        'total_errors': records.aggregate(total=Sum('total_errors'))['total'] or 0,
        'memorized_count': progress.filter(is_memorized=True).count(),
    }

    context = {
        'student': student,
        'records': records[:20],
        'progress': progress,
        'stats': stats,
    }
    return render(request, 'reports/student.html', context)
