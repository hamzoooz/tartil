"""
واجهات التقارير والشهادات
Views for Reports and Certificates
"""
import os
import io
from datetime import datetime, timedelta
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import HttpResponse, JsonResponse, FileResponse
from django.db.models import Avg, Sum, Count
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db.models import Q

from PIL import Image, ImageDraw, ImageFont
from accounts.models import CustomUser, StudentProfile
from recitation.models import RecitationRecord, RecitationError, MemorizationProgress
from halaqat.models import Attendance, Halaqa, HalaqaEnrollment, Session
from .models import CertificateTemplate, Certificate, StudentReport, BulkCertificateGeneration
from .forms import (
    CertificateTemplateForm, CertificateForm, StudentReportForm,
    BulkCertificateForm, CertificatePreviewForm, ReportFilterForm
)


def is_sheikh_or_admin(user):
    """التحقق إذا كان المستخدم شيخاً أو مسؤولاً"""
    return user.is_authenticated and (user.is_sheikh or user.is_admin or user.is_staff)


# ==================== Certificate Template Views ====================

@login_required
@user_passes_test(is_sheikh_or_admin)
def template_list(request):
    """قائمة قوالب الشهادات"""
    templates = CertificateTemplate.objects.all().order_by('-created_at')
    return render(request, 'reports/template_list.html', {'templates': templates})


@login_required
@user_passes_test(is_sheikh_or_admin)
def template_create(request):
    """إنشاء قالب شهادة جديد"""
    if request.method == 'POST':
        form = CertificateTemplateForm(request.POST, request.FILES)
        if form.is_valid():
            template = form.save()
            messages.success(request, _('تم إنشاء قالب الشهادة بنجاح'))
            return redirect('reports:template_preview', pk=template.pk)
    else:
        form = CertificateTemplateForm()
    
    return render(request, 'reports/template_form.html', {
        'form': form,
        'title': _('قالب شهادة جديد')
    })


@login_required
@user_passes_test(is_sheikh_or_admin)
def template_edit(request, pk):
    """تعديل قالب شهادة"""
    template = get_object_or_404(CertificateTemplate, pk=pk)
    
    if request.method == 'POST':
        form = CertificateTemplateForm(request.POST, request.FILES, instance=template)
        if form.is_valid():
            form.save()
            messages.success(request, _('تم تحديث القالب بنجاح'))
            return redirect('reports:template_preview', pk=template.pk)
    else:
        form = CertificateTemplateForm(instance=template)
    
    return render(request, 'reports/template_form.html', {
        'form': form,
        'template': template,
        'title': _('تعديل قالب الشهادة')
    })


@login_required
@user_passes_test(is_sheikh_or_admin)
def template_preview(request, pk):
    """معاينة قالب الشهادة"""
    template = get_object_or_404(CertificateTemplate, pk=pk)
    
    # إنشاء صورة معاينة
    preview_data = {
        'name': _('أحمد محمد عبدالله'),
        'degree': template.default_title or _('شهادة إتمام'),
        'date': timezone.now().strftime('%Y-%m-%d')
    }
    
    return render(request, 'reports/template_preview.html', {
        'template': template,
        'preview': preview_data
    })


@login_required
@user_passes_test(is_sheikh_or_admin)
def template_delete(request, pk):
    """حذف قالب شهادة"""
    template = get_object_or_404(CertificateTemplate, pk=pk)
    
    if request.method == 'POST':
        template.delete()
        messages.success(request, _('تم حذف القالب بنجاح'))
        return redirect('reports:template_list')
    
    return render(request, 'reports/template_confirm_delete.html', {'template': template})


# ==================== Certificate Generation Views ====================

def generate_certificate_image(certificate):
    """توليد صورة الشهادة"""
    template = certificate.template
    
    # فتح صورة القالب
    if not template.template_image:
        return None
    
    try:
        img = Image.open(template.template_image.path)
        draw = ImageDraw.Draw(img)
        
        # الحصول على أبعاد الصورة
        width, height = img.size
        
        # رسم الاسم
        name = certificate.display_name
        name_x = certificate.name_x
        name_y = certificate.name_y
        name_font_size = template.name_font_size
        name_color = template.name_font_color
        
        try:
            name_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", name_font_size)
        except:
            name_font = ImageFont.load_default()
        
        # محاذاة النص في المنتصف
        bbox = draw.textbbox((0, 0), name, font=name_font)
        text_width = bbox[2] - bbox[0]
        name_x = name_x - (text_width // 2)
        
        draw.text((name_x, name_y), name, fill=name_color, font=name_font)
        
        # رسم الدرجة
        degree = certificate.degree_title or template.default_title
        if degree:
            degree_x = certificate.degree_x
            degree_y = certificate.degree_y
            degree_font_size = template.degree_font_size
            degree_color = template.degree_font_color
            
            try:
                degree_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", degree_font_size)
            except:
                degree_font = ImageFont.load_default()
            
            bbox = draw.textbbox((0, 0), degree, font=degree_font)
            text_width = bbox[2] - bbox[0]
            degree_x = degree_x - (text_width // 2)
            
            draw.text((degree_x, degree_y), degree, fill=degree_color, font=degree_font)
        
        # رسم الوصف إذا كان موجوداً
        if certificate.degree_description:
            desc_y = degree_y + 60
            desc_font_size = max(20, template.degree_font_size - 10)
            try:
                desc_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", desc_font_size)
            except:
                desc_font = ImageFont.load_default()
            
            # تقسيم النص الطويل
            words = certificate.degree_description.split()
            lines = []
            current_line = []
            for word in words:
                current_line.append(word)
                test_line = ' '.join(current_line)
                bbox = draw.textbbox((0, 0), test_line, font=desc_font)
                if bbox[2] - bbox[0] > 800:
                    current_line.pop()
                    lines.append(' '.join(current_line))
                    current_line = [word]
            if current_line:
                lines.append(' '.join(current_line))
            
            for i, line in enumerate(lines):
                bbox = draw.textbbox((0, 0), line, font=desc_font)
                text_width = bbox[2] - bbox[0]
                line_x = (width - text_width) // 2
                draw.text((line_x, desc_y + (i * (desc_font_size + 5))), line, 
                         fill=template.degree_font_color, font=desc_font)
        
        # رسم التاريخ
        date_str = certificate.issue_date.strftime('%Y/%m/%d')
        date_x = template.date_position_x
        date_y = template.date_position_y
        date_font_size = template.date_font_size
        date_color = template.date_font_color
        
        try:
            date_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", date_font_size)
        except:
            date_font = ImageFont.load_default()
        
        bbox = draw.textbbox((0, 0), date_str, font=date_font)
        text_width = bbox[2] - bbox[0]
        date_x = date_x - (text_width // 2)
        
        draw.text((date_x, date_y), date_str, fill=date_color, font=date_font)
        
        # رقم الشهادة
        if certificate.certificate_number:
            cert_num = f"#{certificate.certificate_number}"
            try:
                num_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
            except:
                num_font = ImageFont.load_default()
            draw.text((width - 200, height - 50), cert_num, fill='#888888', font=num_font)
        
        # حفظ الصورة
        output = io.BytesIO()
        img.save(output, format='PNG')
        output.seek(0)
        
        return output
        
    except Exception as e:
        print(f"Error generating certificate: {e}")
        return None


@login_required
@user_passes_test(is_sheikh_or_admin)
def certificate_create(request):
    """إنشاء شهادة جديدة"""
    if request.method == 'POST':
        form = CertificateForm(request.POST)
        if form.is_valid():
            certificate = form.save(commit=False)
            certificate.created_by = request.user
            certificate.save()
            
            # توليد صورة الشهادة
            img_data = generate_certificate_image(certificate)
            if img_data:
                from django.core.files.base import ContentFile
                filename = f"certificate_{certificate.certificate_number}.png"
                certificate.generated_file.save(filename, ContentFile(img_data.read()))
                certificate.save()
            
            messages.success(request, _('تم إنشاء الشهادة بنجاح'))
            return redirect('reports:certificate_view', pk=certificate.pk)
    else:
        form = CertificateForm()
        # تحديد قيم افتراضية
        form.fields['issue_date'].initial = timezone.now().date()
    
    return render(request, 'reports/certificate_form.html', {
        'form': form,
        'title': _('إنشاء شهادة جديدة')
    })


@login_required
def certificate_view(request, pk):
    """عرض الشهادة"""
    certificate = get_object_or_404(Certificate, pk=pk)
    
    # التحقق من الصلاحيات
    if not (request.user.is_admin or request.user.is_sheikh or 
            request.user == certificate.student or request.user == certificate.created_by):
        messages.error(request, _('ليس لديك صلاحية لعرض هذه الشهادة'))
        return redirect('core:dashboard')
    
    return render(request, 'reports/certificate_view.html', {
        'certificate': certificate
    })


@login_required
def certificate_download(request, pk):
    """تحميل الشهادة"""
    certificate = get_object_or_404(Certificate, pk=pk)
    
    # التحقق من الصلاحيات
    if not (request.user.is_admin or request.user.is_sheikh or 
            request.user == certificate.student or request.user == certificate.created_by):
        messages.error(request, _('ليس لديك صلاحية لتحميل هذه الشهادة'))
        return redirect('core:dashboard')
    
    # إذا كانت الصورة موجودة
    if certificate.generated_file:
        return FileResponse(
            certificate.generated_file.open(),
            as_attachment=True,
            filename=f"شهادة_{certificate.display_name}_{certificate.certificate_number}.png"
        )
    
    # توليد الصورة إذا لم تكن موجودة
    img_data = generate_certificate_image(certificate)
    if img_data:
        response = HttpResponse(img_data.read(), content_type='image/png')
        response['Content-Disposition'] = f'attachment; filename="شهادة_{certificate.display_name}_{certificate.certificate_number}.png"'
        return response
    
    messages.error(request, _('لا يمكن توليد الشهادة'))
    return redirect('reports:certificate_view', pk=pk)


@login_required
@user_passes_test(is_sheikh_or_admin)
def certificate_list(request):
    """قائمة الشهادات"""
    certificates = Certificate.objects.select_related('student', 'template').order_by('-created_at')
    
    # تصفية حسب الطالب
    student_id = request.GET.get('student')
    if student_id:
        certificates = certificates.filter(student_id=student_id)
    
    # تصفية حسب القالب
    template_id = request.GET.get('template')
    if template_id:
        certificates = certificates.filter(template_id=template_id)
    
    return render(request, 'reports/certificate_list.html', {
        'certificates': certificates,
        'templates': CertificateTemplate.objects.all()
    })


@login_required
@user_passes_test(is_sheikh_or_admin)
def certificate_delete(request, pk):
    """حذف شهادة"""
    certificate = get_object_or_404(Certificate, pk=pk)
    
    if request.method == 'POST':
        certificate.delete()
        messages.success(request, _('تم حذف الشهادة بنجاح'))
        return redirect('reports:certificate_list')
    
    return render(request, 'reports/certificate_confirm_delete.html', {
        'certificate': certificate
    })


# ==================== Bulk Certificate Views ====================

@login_required
@user_passes_test(is_sheikh_or_admin)
def bulk_certificate_create(request):
    """توليد شهادات بالجملة"""
    if request.method == 'POST':
        form = BulkCertificateForm(request.POST)
        if form.is_valid():
            bulk = form.save(commit=False)
            bulk.created_by = request.user
            bulk.save()
            
            # توليد الشهادات
            count = bulk.generate_certificates()
            messages.success(request, _('تم توليد {} شهادة بنجاح').format(count))
            return redirect('reports:certificate_list')
    else:
        form = BulkCertificateForm()
    
    return render(request, 'reports/bulk_certificate_form.html', {
        'form': form,
        'title': _('توليد شهادات بالجملة')
    })


@login_required
@user_passes_test(is_sheikh_or_admin)
def ajax_preview_certificate(request):
    """معاينة الشهادة عبر AJAX"""
    template_id = request.GET.get('template')
    name = request.GET.get('name', _('أحمد محمد'))
    degree = request.GET.get('degree', _('شهادة إتمام'))
    
    if not template_id:
        return JsonResponse({'error': 'Template ID required'}, status=400)
    
    try:
        template = CertificateTemplate.objects.get(pk=template_id)
        
        # إنشاء شهادة مؤقتة للمعاينة
        class PreviewCert:
            def __init__(self, template, name, degree):
                self.template = template
                self.custom_name = name
                self.degree_title = degree
                self.issue_date = timezone.now().date()
                self.certificate_number = 'PREVIEW'
            
            def display_name(self):
                return self.custom_name
            
            @property
            def name_x(self):
                return template.name_position_x
            
            @property
            def name_y(self):
                return template.name_position_y
            
            @property
            def degree_x(self):
                return template.degree_position_x
            
            @property
            def degree_y(self):
                return template.degree_position_y
        
        preview_cert = PreviewCert(template, name, degree)
        
        img_data = generate_certificate_image(preview_cert)
        if img_data:
            import base64
            img_base64 = base64.b64encode(img_data.read()).decode('utf-8')
            return JsonResponse({
                'image': f'data:image/png;base64,{img_base64}'
            })
        
        return JsonResponse({'error': 'Failed to generate preview'}, status=500)
        
    except CertificateTemplate.DoesNotExist:
        return JsonResponse({'error': 'Template not found'}, status=404)


# ==================== Student Report Views ====================

@login_required
def student_report_list(request):
    """قائمة تقارير الطلاب"""
    reports = StudentReport.objects.select_related('student').order_by('-created_at')
    
    # إذا كان طالباً، اعرض تقاريره فقط
    if request.user.is_student:
        reports = reports.filter(student=request.user)
    
    # تصفية
    form = ReportFilterForm(request.GET)
    if form.is_valid():
        data = form.cleaned_data
        if data.get('student'):
            reports = reports.filter(student=data['student'])
        if data.get('period'):
            reports = reports.filter(report_period=data['period'])
        if data.get('start_date'):
            reports = reports.filter(start_date__gte=data['start_date'])
        if data.get('end_date'):
            reports = reports.filter(end_date__lte=data['end_date'])
    
    return render(request, 'reports/report_list.html', {
        'reports': reports,
        'filter_form': form
    })


@login_required
@user_passes_test(is_sheikh_or_admin)
def student_report_create(request):
    """إنشاء تقرير طالب"""
    if request.method == 'POST':
        form = StudentReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.created_by = request.user
            report.save()
            
            # توليد الإحصائيات تلقائياً إذا طُلب ذلك
            if form.cleaned_data.get('auto_generate'):
                report.generate_statistics()
            
            messages.success(request, _('تم إنشاء التقرير بنجاح'))
            return redirect('reports:report_view', pk=report.pk)
    else:
        # تعيين تواريخ افتراضية (الشهر الحالي)
        today = timezone.now().date()
        first_day = today.replace(day=1)
        
        form = StudentReportForm(initial={
            'start_date': first_day,
            'end_date': today
        })
    
    return render(request, 'reports/report_form.html', {
        'form': form,
        'title': _('إنشاء تقرير طالب')
    })


@login_required
def student_report_view(request, pk):
    """عرض تقرير طالب"""
    report = get_object_or_404(StudentReport, pk=pk)
    
    # التحقق من الصلاحيات
    if not (request.user.is_admin or request.user.is_sheikh or 
            request.user == report.student):
        messages.error(request, _('ليس لديك صلاحية لعرض هذا التقرير'))
        return redirect('core:dashboard')
    
    # الحصول على البيانات التفصيلية
    detailed_data = report.detailed_data or {}
    
    return render(request, 'reports/report_view.html', {
        'report': report,
        'detailed_data': detailed_data
    })


@login_required
@user_passes_test(is_sheikh_or_admin)
def student_report_delete(request, pk):
    """حذف تقرير"""
    report = get_object_or_404(StudentReport, pk=pk)
    
    if request.method == 'POST':
        report.delete()
        messages.success(request, _('تم حذف التقرير بنجاح'))
        return redirect('reports:report_list')
    
    return render(request, 'reports/report_confirm_delete.html', {'report': report})


# ==================== Student Statistics API ====================

@login_required
def ajax_get_student_stats(request):
    """الحصول على إحصائيات الطالب عبر AJAX"""
    student_id = request.GET.get('student')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if not student_id:
        return JsonResponse({'error': 'Student ID required'}, status=400)
    
    try:
        student = CustomUser.objects.get(pk=student_id, user_type='student')
        
        # تحويل التواريخ
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        else:
            start_date = timezone.now().date() - timedelta(days=30)
        
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        else:
            end_date = timezone.now().date()
        
        # إحصائيات التسميع
        recitations = RecitationRecord.objects.filter(
            student=student,
            created_at__date__range=[start_date, end_date]
        )
        
        total_recitations = recitations.count()
        avg_grade = recitations.aggregate(Avg('grade'))['grade__avg'] or 0
        
        # الصفحات المحفوظة والمراجعة
        new_pages = recitations.filter(recitation_type='new').count()
        review_pages = recitations.filter(recitation_type='review').count()
        
        # الأخطاء
        errors = RecitationError.objects.filter(
            record__student=student,
            created_at__date__range=[start_date, end_date]
        )
        total_errors = errors.count()
        
        # الحضور
        attendances = Attendance.objects.filter(
            student=student,
            session__date__range=[start_date, end_date]
        )
        total_sessions = attendances.count()
        present_sessions = attendances.filter(status='present').count()
        attendance_rate = round((present_sessions / total_sessions * 100), 2) if total_sessions > 0 else 0
        
        return JsonResponse({
            'total_recitations': total_recitations,
            'average_grade': round(avg_grade, 1),
            'total_pages_memorized': new_pages,
            'total_pages_reviewed': review_pages,
            'total_errors': total_errors,
            'total_sessions': total_sessions,
            'attendance_rate': attendance_rate,
            'student_name': student.get_full_name()
        })
        
    except CustomUser.DoesNotExist:
        return JsonResponse({'error': 'Student not found'}, status=404)


# ==================== Dashboard Reports ====================

@login_required
def my_reports(request):
    """تقاريري (للطالب)"""
    if not request.user.is_student:
        messages.error(request, _('هذه الصفحة للطلاب فقط'))
        return redirect('core:dashboard')
    
    # آخر تقرير
    latest_report = StudentReport.objects.filter(
        student=request.user
    ).first()
    
    # آخر شهادة
    latest_certificate = Certificate.objects.filter(
        student=request.user,
        status='issued'
    ).first()
    
    # إحصائيات الشهر الحالي
    today = timezone.now().date()
    first_day = today.replace(day=1)
    
    recitations = RecitationRecord.objects.filter(
        student=request.user,
        created_at__date__range=[first_day, today]
    )
    
    monthly_stats = {
        'total_recitations': recitations.count(),
        'average_grade': round(recitations.aggregate(Avg('grade'))['grade__avg'] or 0, 1),
        'new_memorization': recitations.filter(recitation_type='new').count(),
        'review': recitations.filter(recitation_type='review').count(),
    }
    
    return render(request, 'reports/my_reports.html', {
        'latest_report': latest_report,
        'latest_certificate': latest_certificate,
        'monthly_stats': monthly_stats
    })
