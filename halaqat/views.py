"""
Halaqat Views
صفحات الحلقات
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Course, Halaqa, HalaqaEnrollment, Session, Attendance


def halaqa_list(request):
    """قائمة الحلقات"""
    halaqat = Halaqa.objects.filter(status='active', is_private=False)

    # البحث
    search = request.GET.get('search')
    if search:
        halaqat = halaqat.filter(
            Q(name__icontains=search) |
            Q(sheikh__first_name__icontains=search) |
            Q(sheikh__last_name__icontains=search)
        )

    # فلتر المسار
    course_id = request.GET.get('course')
    if course_id:
        halaqat = halaqat.filter(course_id=course_id)

    # الترقيم
    paginator = Paginator(halaqat, 12)
    page = request.GET.get('page')
    halaqat = paginator.get_page(page)

    courses = Course.objects.filter(is_active=True)

    context = {
        'halaqat': halaqat,
        'courses': courses,
    }
    return render(request, 'halaqat/list.html', context)


def halaqa_detail(request, pk):
    """تفاصيل الحلقة"""
    halaqa = get_object_or_404(Halaqa, pk=pk)
    enrollments = halaqa.enrollments.filter(status='active').select_related('student')

    # التحقق من تسجيل المستخدم
    is_enrolled = False
    if request.user.is_authenticated:
        is_enrolled = HalaqaEnrollment.objects.filter(
            student=request.user, halaqa=halaqa
        ).exists()

    context = {
        'halaqa': halaqa,
        'enrollments': enrollments,
        'is_enrolled': is_enrolled,
    }
    return render(request, 'halaqat/detail.html', context)


@login_required
def enroll(request, pk):
    """الانضمام لحلقة"""
    halaqa = get_object_or_404(Halaqa, pk=pk)

    if not request.user.is_student:
        messages.error(request, 'فقط الطلاب يمكنهم الانضمام للحلقات')
        return redirect('halaqat:detail', pk=pk)

    if halaqa.is_full:
        messages.error(request, 'الحلقة مكتملة العدد')
        return redirect('halaqat:detail', pk=pk)

    enrollment, created = HalaqaEnrollment.objects.get_or_create(
        student=request.user,
        halaqa=halaqa,
        defaults={'status': 'active'}
    )

    if created:
        messages.success(request, f'تم تسجيلك في حلقة {halaqa.name} بنجاح')
    else:
        messages.info(request, 'أنت مسجل بالفعل في هذه الحلقة')

    return redirect('halaqat:detail', pk=pk)


@login_required
def my_halaqat(request):
    """حلقاتي"""
    if request.user.is_student:
        enrollments = HalaqaEnrollment.objects.filter(
            student=request.user
        ).select_related('halaqa', 'halaqa__sheikh')
        return render(request, 'halaqat/my_halaqat.html', {'enrollments': enrollments})
    elif request.user.is_sheikh:
        halaqat = Halaqa.objects.filter(sheikh=request.user)
        return render(request, 'halaqat/manage.html', {'halaqat': halaqat})

    return redirect('core:dashboard')


@login_required
def manage_halaqat(request):
    """إدارة الحلقات (للشيخ)"""
    if not request.user.is_sheikh:
        messages.error(request, 'هذه الصفحة للمشايخ فقط')
        return redirect('core:dashboard')

    halaqat = Halaqa.objects.filter(sheikh=request.user)
    return render(request, 'halaqat/manage.html', {'halaqat': halaqat})


@login_required
def create_halaqa(request):
    """إنشاء حلقة جديدة"""
    if not (request.user.is_sheikh or request.user.is_admin):
        messages.error(request, 'غير مصرح لك بإنشاء حلقة')
        return redirect('halaqat:list')

    if request.method == 'POST':
        halaqa = Halaqa.objects.create(
            name=request.POST.get('name'),
            sheikh=request.user,
            course_id=request.POST.get('course') or None,
            description=request.POST.get('description', ''),
            max_students=int(request.POST.get('max_students', 10)),
            schedule_days=request.POST.get('schedule_days', ''),
            meet_link=request.POST.get('meet_link', ''),
        )
        messages.success(request, f'تم إنشاء حلقة {halaqa.name} بنجاح')
        return redirect('halaqat:detail', pk=halaqa.pk)

    courses = Course.objects.filter(is_active=True)
    return render(request, 'halaqat/create.html', {'courses': courses})


@login_required
def sessions_list(request):
    """قائمة الجلسات"""
    if request.user.is_sheikh:
        halaqat = Halaqa.objects.filter(sheikh=request.user)
        sessions = Session.objects.filter(halaqa__in=halaqat).order_by('-date')
    elif request.user.is_student:
        enrollments = HalaqaEnrollment.objects.filter(student=request.user, status='active')
        halaqat_ids = enrollments.values_list('halaqa_id', flat=True)
        sessions = Session.objects.filter(halaqa_id__in=halaqat_ids).order_by('-date')
    else:
        sessions = Session.objects.all().order_by('-date')

    return render(request, 'halaqat/sessions.html', {'sessions': sessions})


@login_required
def all_halaqat(request):
    """جميع الحلقات (للإدارة)"""
    if not request.user.is_admin:
        messages.error(request, 'هذه الصفحة للإدارة فقط')
        return redirect('core:dashboard')

    halaqat = Halaqa.objects.all().select_related('sheikh', 'course')
    return render(request, 'halaqat/all.html', {'halaqat': halaqat})
