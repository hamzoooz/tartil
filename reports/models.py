"""
نماذج التقارير والشهادات
Reports and Certificates Models for Tartil
"""
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import os


class CertificateTemplate(models.Model):
    """نموذج قالب الشهادة"""
    
    name = models.CharField(_('اسم القالب'), max_length=200)
    description = models.TextField(_('الوصف'), blank=True)
    template_image = models.ImageField(
        _('صورة القالب'),
        upload_to='certificates/templates/',
        help_text=_('ارفع صورة خلفية الشهادة (مثلاً: JPG, PNG)')
    )
    is_active = models.BooleanField(_('نشط'), default=True)
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    updated_at = models.DateTimeField(_('تاريخ التحديث'), auto_now=True)
    
    # إعدادات الخط للاسم
    name_font_size = models.PositiveIntegerField(_('حجم خط الاسم'), default=48)
    name_font_color = models.CharField(_('لون خط الاسم'), max_length=20, default='#000000')
    name_position_x = models.PositiveIntegerField(_('موقع الاسم X'), default=540)
    name_position_y = models.PositiveIntegerField(_('موقع الاسم Y'), default=400)
    name_font_family = models.CharField(_('خط الاسم'), max_length=100, default='Arial', blank=True)
    
    # إعدادات الخط للدرجة/الإنجاز
    degree_font_size = models.PositiveIntegerField(_('حجم خط الدرجة'), default=36)
    degree_font_color = models.CharField(_('لون خط الدرجة'), max_length=20, default='#333333')
    degree_position_x = models.PositiveIntegerField(_('موقع الدرجة X'), default=540)
    degree_position_y = models.PositiveIntegerField(_('موقع الدرجة Y'), default=500)
    degree_font_family = models.CharField(_('خط الدرجة'), max_length=100, default='Arial', blank=True)
    
    # إعدادات الخط للتاريخ
    date_font_size = models.PositiveIntegerField(_('حجم خط التاريخ'), default=24)
    date_font_color = models.CharField(_('لون خط التاريخ'), max_length=20, default='#666666')
    date_position_x = models.PositiveIntegerField(_('موقع التاريخ X'), default=540)
    date_position_y = models.PositiveIntegerField(_('موقع التاريخ Y'), default=600)
    date_font_family = models.CharField(_('خط التاريخ'), max_length=100, default='Arial', blank=True)
    
    # نصوص افتراضية
    default_title = models.CharField(_('عنوان الشهادة الافتراضي'), max_length=200, 
                                     default='شهادة إتمام', blank=True)
    default_description = models.TextField(_('وصف الإنجاز الافتراضي'),
                                           default='تم منح هذه الشهادة تقديراً لإتمام', blank=True)
    
    class Meta:
        verbose_name = _('قالب شهادة')
        verbose_name_plural = _('قوالب الشهادات')
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name


class Certificate(models.Model):
    """نموذج الشهادة الممنوحة"""
    
    class CertificateStatus(models.TextChoices):
        DRAFT = 'draft', _('مسودة')
        ISSUED = 'issued', _('صادرة')
        REVOKED = 'revoked', _('ملغاة')
    
    template = models.ForeignKey(
        CertificateTemplate,
        on_delete=models.CASCADE,
        related_name='certificates',
        verbose_name=_('القالب')
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='certificates',
        limit_choices_to={'user_type': 'student'},
        verbose_name=_('الطالب')
    )
    certificate_number = models.CharField(_('رقم الشهادة'), max_length=50, unique=True, blank=True)
    
    # البيانات المخصصة
    custom_name = models.CharField(_('الاسم على الشهادة'), max_length=200, blank=True,
                                   help_text=_('اتركه فارغاً لاستخدام اسم الطلبة الافتراضي'))
    degree_title = models.CharField(_('عنوان الدرجة/الإنجاز'), max_length=200, blank=True)
    degree_description = models.TextField(_('وصف الإنجاز'), blank=True)
    issue_date = models.DateField(_('تاريخ الإصدار'), default=timezone.now)
    
    # حالة الشهادة والملف
    status = models.CharField(
        _('الحالة'),
        max_length=20,
        choices=CertificateStatus.choices,
        default=CertificateStatus.ISSUED
    )
    generated_file = models.FileField(
        _('ملف الشهادة'),
        upload_to='certificates/generated/',
        blank=True,
        null=True
    )
    
    # بيانات التخصيص (تجاوز للقالب)
    name_position_x_override = models.PositiveIntegerField(_('X الاسم (تجاوز)'), null=True, blank=True)
    name_position_y_override = models.PositiveIntegerField(_('Y الاسم (تجاوز)'), null=True, blank=True)
    degree_position_x_override = models.PositiveIntegerField(_('X الدرجة (تجاوز)'), null=True, blank=True)
    degree_position_y_override = models.PositiveIntegerField(_('Y الدرجة (تجاوز)'), null=True, blank=True)
    
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    updated_at = models.DateTimeField(_('تاريخ التحديث'), auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_certificates',
        verbose_name=_('أنشئت بواسطة')
    )
    
    class Meta:
        verbose_name = _('شهادة')
        verbose_name_plural = _('الشهادات')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.certificate_number or 'بدون رقم'}"
    
    def save(self, *args, **kwargs):
        if not self.certificate_number:
            # توليد رقم الشهادة تلقائياً
            year = timezone.now().year
            count = Certificate.objects.filter(created_at__year=year).count() + 1
            self.certificate_number = f"TARTIL-{year}-{count:05d}"
        super().save(*args, **kwargs)
    
    @property
    def display_name(self):
        return self.custom_name or self.student.get_full_name()
    
    @property
    def name_x(self):
        return self.name_position_x_override or self.template.name_position_x
    
    @property
    def name_y(self):
        return self.name_position_y_override or self.template.name_position_y
    
    @property
    def degree_x(self):
        return self.degree_position_x_override or self.template.degree_position_x
    
    @property
    def degree_y(self):
        return self.degree_position_y_override or self.template.degree_position_y


class StudentReport(models.Model):
    """نموذج تقرير الطالب"""
    
    class ReportPeriod(models.TextChoices):
        WEEKLY = 'weekly', _('أسبوعي')
        MONTHLY = 'monthly', _('شهري')
        QUARTERLY = 'quarterly', _('ربع سنوي')
        YEARLY = 'yearly', _('سنوي')
        CUSTOM = 'custom', _('مخصص')
    
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reports',
        limit_choices_to={'user_type': 'student'},
        verbose_name=_('الطالب')
    )
    report_period = models.CharField(
        _('فترة التقرير'),
        max_length=20,
        choices=ReportPeriod.choices,
        default=ReportPeriod.MONTHLY
    )
    start_date = models.DateField(_('تاريخ البداية'))
    end_date = models.DateField(_('تاريخ النهاية'))
    
    # إحصائيات الحفظ
    total_sessions = models.PositiveIntegerField(_('عدد الجلسات'), default=0)
    total_recitations = models.PositiveIntegerField(_('عدد التسميعات'), default=0)
    total_pages_memorized = models.PositiveIntegerField(_('الصفحات المحفوظة'), default=0)
    total_pages_reviewed = models.PositiveIntegerField(_('الصفحات المراجعة'), default=0)
    average_grade = models.DecimalField(_('متوسط الدرجة'), max_digits=4, decimal_places=1, default=0)
    attendance_rate = models.DecimalField(_('نسبة الحضور'), max_digits=5, decimal_places=2, default=0)
    
    # إحصائيات الأخطاء
    total_errors = models.PositiveIntegerField(_('إجمالي الأخطاء'), default=0)
    tajweed_errors = models.PositiveIntegerField(_('أخطاء التجويد'), default=0)
    memorization_errors = models.PositiveIntegerField(_('أخطاء الحفظ'), default=0)
    
    # التقييم العام
    general_evaluation = models.TextField(_('التقييم العام'), blank=True)
    recommendations = models.TextField(_('التوصيات'), blank=True)
    
    # البيانات التفصيلية (تُحسب تلقائياً)
    detailed_data = models.JSONField(_('البيانات التفصيلية'), default=dict, blank=True)
    
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_reports',
        verbose_name=_('أنشئ بواسطة')
    )
    
    class Meta:
        verbose_name = _('تقرير طالب')
        verbose_name_plural = _('تقارير الطلاب')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.get_report_period_display()} - {self.start_date} إلى {self.end_date}"
    
    def generate_statistics(self):
        """توليد الإحصائيات من البيانات الفعلية"""
        from recitation.models import RecitationRecord, RecitationError
        from halaqat.models import Attendance
        from django.db.models import Avg, Sum, Count
        
        # إحصائيات التسميع
        recitations = RecitationRecord.objects.filter(
            student=self.student,
            created_at__date__range=[self.start_date, self.end_date]
        )
        
        self.total_recitations = recitations.count()
        avg_grade = recitations.aggregate(Avg('grade'))['grade__avg']
        self.average_grade = round(avg_grade or 0, 1)
        
        # عدد الصفحات المحفوظة والمراجعة
        new_memorization = recitations.filter(recitation_type='new').count()
        review = recitations.filter(recitation_type='review').count()
        self.total_pages_memorized = new_memorization
        self.total_pages_reviewed = review
        
        # إحصائيات الأخطاء
        errors = RecitationError.objects.filter(
            record__student=self.student,
            created_at__date__range=[self.start_date, self.end_date]
        )
        self.total_errors = errors.count()
        self.tajweed_errors = errors.filter(error_type='tajweed').count()
        self.memorization_errors = errors.filter(error_type__in=['forget', 'addition', 'replacement']).count()
        
        # إحصائيات الحضور
        attendances = Attendance.objects.filter(
            student=self.student,
            session__date__range=[self.start_date, self.end_date]
        )
        total_attendance = attendances.count()
        if total_attendance > 0:
            present_count = attendances.filter(status='present').count()
            self.attendance_rate = round((present_count / total_attendance) * 100, 2)
        else:
            self.attendance_rate = 0
        
        self.total_sessions = total_attendance
        
        # حفظ البيانات التفصيلية
        self.detailed_data = {
            'recitation_details': list(recitations.values(
                'created_at', 'surah_start__name_arabic', 'grade', 'grade_level'
            )),
            'error_breakdown': list(errors.values('error_type').annotate(count=Count('id'))),
            'daily_progress': list(recitations.values('created_at__date').annotate(
                count=Count('id'),
                avg_grade=Avg('grade')
            ))
        }
        
        self.save()


class BulkCertificateGeneration(models.Model):
    """نموذج توليد شهادات بالجملة"""
    
    template = models.ForeignKey(
        CertificateTemplate,
        on_delete=models.CASCADE,
        related_name='bulk_generations',
        verbose_name=_('القالب')
    )
    halaqa = models.ForeignKey(
        'halaqat.Halaqa',
        on_delete=models.CASCADE,
        related_name='bulk_certificates',
        verbose_name=_('الحلقة'),
        null=True,
        blank=True
    )
    degree_title = models.CharField(_('عنوان الدرجة'), max_length=200)
    degree_description = models.TextField(_('وصف الإنجاز'), blank=True)
    issue_date = models.DateField(_('تاريخ الإصدار'), default=timezone.now)
    
    # خيارات التصفية
    min_grade = models.DecimalField(_('الحد الأدنى للدرجة'), max_digits=4, decimal_places=1, 
                                    default=0, help_text=_('توليد شهادات للطلاب بدرجة أعلى من هذا'))
    min_attendance_rate = models.DecimalField(_('الحد الأدنى للحضور'), max_digits=5, decimal_places=2,
                                              default=0, help_text=_('نسبة الحضور المطلوبة'))
    
    generated_count = models.PositiveIntegerField(_('عدد الشهادات المولدة'), default=0)
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='bulk_generations',
        verbose_name=_('أنشئ بواسطة')
    )
    
    class Meta:
        verbose_name = _('توليد شهادات بالجملة')
        verbose_name_plural = _('توليد الشهادات بالجملة')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"توليد شهادات - {self.template.name} - {self.created_at.strftime('%Y-%m-%d')}"
    
    def generate_certificates(self):
        """توليد الشهادات للطلاب المستحقين"""
        from halaqat.models import HalaqaEnrollment
        from recitation.models import RecitationRecord
        from django.db.models import Avg
        
        students_to_generate = []
        
        if self.halaqa:
            enrollments = HalaqaEnrollment.objects.filter(
                halaqa=self.halaqa,
                status='active'
            )
            for enrollment in enrollments:
                student = enrollment.student
                # حساب متوسط درجات الطالب
                avg_grade = RecitationRecord.objects.filter(
                    student=student
                ).aggregate(Avg('grade'))['grade__avg'] or 0
                
                if avg_grade >= self.min_grade:
                    students_to_generate.append(student)
        else:
            # جميع الطلاب النشطين
            from accounts.models import CustomUser
            students_to_generate = CustomUser.objects.filter(
                user_type='student',
                is_active=True
            )
        
        count = 0
        for student in students_to_generate:
            Certificate.objects.create(
                template=self.template,
                student=student,
                degree_title=self.degree_title,
                degree_description=self.degree_description,
                issue_date=self.issue_date,
                created_by=self.created_by
            )
            count += 1
        
        self.generated_count = count
        self.save()
        return count
