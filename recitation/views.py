"""
Recitation Views
صفحات التسميع
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Avg, Count
from .models import RecitationRecord, RecitationError, MemorizationProgress, DailyGoal


@login_required
def my_records(request):
    """سجلات التسميع الخاصة بي"""
    records = RecitationRecord.objects.filter(
        student=request.user
    ).select_related('session', 'surah_start', 'surah_end').order_by('-created_at')

    context = {
        'records': records,
    }
    return render(request, 'recitation/my_records.html', context)


@login_required
def record_detail(request, pk):
    """تفاصيل سجل التسميع"""
    record = get_object_or_404(RecitationRecord, pk=pk)

    # التحقق من الصلاحية
    if record.student != request.user and not (request.user.is_sheikh or request.user.is_admin):
        messages.error(request, 'غير مصرح لك بعرض هذا السجل')
        return redirect('recitation:my_records')

    errors = record.errors.all()

    context = {
        'record': record,
        'errors': errors,
    }
    return render(request, 'recitation/record_detail.html', context)


@login_required
def progress(request):
    """تقدم الحفظ"""
    if not request.user.is_student:
        return redirect('core:dashboard')

    progress_list = MemorizationProgress.objects.filter(
        student=request.user
    ).select_related('surah').order_by('surah__number')

    # إحصائيات
    stats = {
        'total_memorized': progress_list.filter(is_memorized=True).count(),
        'total_reviewed': progress_list.filter(is_reviewed=True).count(),
        'average_grade': progress_list.aggregate(avg=Avg('average_grade'))['avg'] or 0,
    }

    context = {
        'progress_list': progress_list,
        'stats': stats,
    }
    return render(request, 'recitation/progress.html', context)


@login_required
def evaluate(request):
    """صفحة التقييم (للشيخ)"""
    if not request.user.is_sheikh:
        messages.error(request, 'هذه الصفحة للمشايخ فقط')
        return redirect('core:dashboard')

    # الحصول على طلاب الشيخ
    from halaqat.models import Halaqa, HalaqaEnrollment
    halaqat = Halaqa.objects.filter(sheikh=request.user)
    enrollments = HalaqaEnrollment.objects.filter(
        halaqa__in=halaqat, status='active'
    ).select_related('student', 'halaqa')

    context = {
        'enrollments': enrollments,
    }
    return render(request, 'recitation/evaluate.html', context)


@login_required
def create_record(request, session_id):
    """إنشاء سجل تسميع جديد"""
    if not request.user.is_sheikh:
        messages.error(request, 'هذه الصفحة للمشايخ فقط')
        return redirect('core:dashboard')

    from halaqat.models import Session
    session = get_object_or_404(Session, pk=session_id)

    if request.method == 'POST':
        from quran.models import Surah

        record = RecitationRecord.objects.create(
            student_id=request.POST.get('student'),
            session=session,
            surah_start_id=request.POST.get('surah_start'),
            ayah_start=int(request.POST.get('ayah_start', 1)),
            surah_end_id=request.POST.get('surah_end'),
            ayah_end=int(request.POST.get('ayah_end', 1)),
            recitation_type=request.POST.get('recitation_type', 'new'),
            grade=float(request.POST.get('grade', 0)),
            notes=request.POST.get('notes', ''),
            sheikh_feedback=request.POST.get('feedback', ''),
        )

        messages.success(request, 'تم تسجيل التسميع بنجاح')
        return redirect('recitation:record_detail', pk=record.pk)

    from quran.models import Surah
    from halaqat.models import HalaqaEnrollment

    students = HalaqaEnrollment.objects.filter(
        halaqa=session.halaqa, status='active'
    ).select_related('student')
    surahs = Surah.objects.all()

    context = {
        'session': session,
        'students': students,
        'surahs': surahs,
    }
    return render(request, 'recitation/create_record.html', context)


@login_required
def daily_goals(request):
    """الأهداف اليومية"""
    if not request.user.is_student:
        return redirect('core:dashboard')

    from datetime import date, timedelta
    today = date.today()

    # الأهداف لآخر 30 يوم
    goals = DailyGoal.objects.filter(
        student=request.user,
        date__gte=today - timedelta(days=30)
    ).order_by('-date')

    # هدف اليوم
    today_goal, created = DailyGoal.objects.get_or_create(
        student=request.user,
        date=today,
        defaults={
            'target_new_lines': 5,
            'target_review_pages': 2,
        }
    )

    context = {
        'goals': goals,
        'today_goal': today_goal,
    }
    return render(request, 'recitation/daily_goals.html', context)
