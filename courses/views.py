"""
Views for Courses app
مشاهد المقررات والدروس
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Q
from datetime import date, timedelta

from .models import (
    Curriculum, CurriculumLesson, StudentCurriculum,
    MotivationalQuote, TafseerLesson, ScheduledNotification,
    LessonReminder
)


def curriculum_list(request):
    """عرض قائمة المقررات المتاحة"""
    curriculums = Curriculum.objects.filter(is_active=True)
    
    # إحصائيات
    context = {
        'curriculums': curriculums,
        'total_count': curriculums.count(),
    }
    return render(request, 'courses/curriculum_list.html', context)


def curriculum_detail(request, pk):
    """تفاصيل المقرر"""
    curriculum = get_object_or_404(Curriculum, pk=pk, is_active=True)
    lessons = curriculum.lessons.filter(is_active=True)
    
    # التحقق من تسجيل الطالب
    is_enrolled = False
    student_curriculum = None
    if request.user.is_authenticated and request.user.is_student:
        student_curriculum = StudentCurriculum.objects.filter(
            student=request.user,
            curriculum=curriculum
        ).first()
        is_enrolled = student_curriculum is not None
    
    context = {
        'curriculum': curriculum,
        'lessons': lessons,
        'is_enrolled': is_enrolled,
        'student_curriculum': student_curriculum,
        'total_lessons': lessons.count(),
    }
    return render(request, 'courses/curriculum_detail.html', context)


@login_required
def curriculum_enroll(request, pk):
    """تسجيل الطالب في المقرر"""
    curriculum = get_object_or_404(Curriculum, pk=pk, is_active=True)
    
    if not request.user.is_student:
        messages.error(request, 'عذراً، هذا القسم مخصص للطلاب فقط')
        return redirect('courses:detail', pk=pk)
    
    # التحقق من عدم التسجيل مسبقاً
    existing = StudentCurriculum.objects.filter(
        student=request.user,
        curriculum=curriculum
    ).first()
    
    if existing:
        messages.info(request, 'أنت مسجل بالفعل في هذا المقرر')
        return redirect('courses:detail', pk=pk)
    
    # إنشاء تسجيل جديد
    student_curriculum = StudentCurriculum.objects.create(
        student=request.user,
        curriculum=curriculum,
        status=StudentCurriculum.Status.NOT_STARTED,
        start_date=date.today()
    )
    
    messages.success(request, f'تم تسجيلك في المقرر "{curriculum.name}" بنجاح')
    return redirect('courses:detail', pk=pk)


def lesson_detail(request, pk):
    """تفاصيل الدرس"""
    lesson = get_object_or_404(CurriculumLesson, pk=pk, is_active=True)
    
    context = {
        'lesson': lesson,
        'curriculum': lesson.curriculum,
    }
    return render(request, 'courses/lesson_detail.html', context)


@login_required
def lesson_complete(request, pk):
    """إكمال الدرس"""
    lesson = get_object_or_404(CurriculumLesson, pk=pk, is_active=True)
    
    if not request.user.is_student:
        messages.error(request, 'عذراً، هذا القسم مخصص للطلاب فقط')
        return redirect('courses:lesson_detail', pk=pk)
    
    # تحديث الدرس الحالي للطالب
    student_curriculum = StudentCurriculum.objects.filter(
        student=request.user,
        curriculum=lesson.curriculum
    ).first()
    
    if student_curriculum:
        student_curriculum.current_lesson = lesson
        student_curriculum.status = StudentCurriculum.Status.IN_PROGRESS
        student_curriculum.save()
        messages.success(request, 'تم تحديد الدرس كمكتمل')
    
    return redirect('courses:lesson_detail', pk=pk)


def quote_list(request):
    """قائمة الكلمات التحفيزية"""
    # الكلمات المنشورة فقط
    quotes = MotivationalQuote.objects.filter(
        is_active=True,
        is_published=True
    ).order_by('-published_at')
    
    # تصفية حسب التصنيف
    category = request.GET.get('category')
    if category:
        quotes = quotes.filter(category=category)
    
    context = {
        'quotes': quotes,
        'categories': MotivationalQuote.QuoteCategory.choices,
    }
    return render(request, 'courses/quote_list.html', context)


def quote_detail(request, pk):
    """تفاصيل الكلمة التحفيزية"""
    quote = get_object_or_404(
        MotivationalQuote,
        pk=pk,
        is_active=True,
        is_published=True
    )
    
    # زيادة عدد المشاهدات
    quote.view_count += 1
    quote.save(update_fields=['view_count'])
    
    context = {
        'quote': quote,
    }
    return render(request, 'courses/quote_detail.html', context)


def tafseer_list(request):
    """قائمة دروس التفسير"""
    lessons = TafseerLesson.objects.filter(
        is_active=True,
        is_published=True
    ).order_by('surah__number', 'ayah_from')
    
    context = {
        'lessons': lessons,
    }
    return render(request, 'courses/tafseer_list.html', context)


def tafseer_detail(request, pk):
    """تفاصيل درس التفسير"""
    lesson = get_object_or_404(
        TafseerLesson,
        pk=pk,
        is_active=True,
        is_published=True
    )
    
    # زيادة عدد المشاهدات
    lesson.view_count += 1
    lesson.save(update_fields=['view_count'])
    
    context = {
        'lesson': lesson,
    }
    return render(request, 'courses/tafseer_detail.html', context)


@login_required
def api_my_curriculums(request):
    """API: مقررات الطالب"""
    if not request.user.is_student:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    curriculums = StudentCurriculum.objects.filter(
        student=request.user
    ).select_related('curriculum', 'current_lesson')
    
    data = []
    for item in curriculums:
        data.append({
            'id': item.curriculum.id,
            'name': item.curriculum.name,
            'status': item.get_status_display(),
            'progress': item.get_progress_percentage(),
            'current_lesson': item.current_lesson.title if item.current_lesson else None,
            'start_date': item.start_date.isoformat() if item.start_date else None,
        })
    
    return JsonResponse({'curriculums': data})


@login_required
def api_today_lessons(request):
    """API: دروس اليوم للطالب"""
    if not request.user.is_student:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    today = date.today()
    
    # الحصول على تذكيرات اليوم
    reminders = LessonReminder.objects.filter(
        student_curriculum__student=request.user,
        scheduled_date=today,
        is_completed=False
    ).select_related('lesson', 'student_curriculum__curriculum')
    
    data = []
    for reminder in reminders:
        data.append({
            'lesson_id': reminder.lesson.id,
            'lesson_title': reminder.lesson.title,
            'curriculum_name': reminder.student_curriculum.curriculum.name,
            'scheduled_time': reminder.scheduled_time.strftime('%H:%M'),
        })
    
    return JsonResponse({'lessons': data})


@login_required
def my_notifications(request):
    """إشعارات الطالب"""
    from accounts.models import Notification
    
    notifications = Notification.objects.filter(
        user=request.user
    ).order_by('-created_at')
    
    # تحديث حالة القراءة
    unread_count = notifications.filter(is_read=False).count()
    
    context = {
        'notifications': notifications[:50],
        'unread_count': unread_count,
    }
    return render(request, 'courses/notifications.html', context)


@login_required
@require_POST
def mark_notification_read(request, pk):
    """تحديد الإشعار كمقروء"""
    from accounts.models import Notification
    
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.is_read = True
    notification.save(update_fields=['is_read'])
    
    return JsonResponse({'success': True})
