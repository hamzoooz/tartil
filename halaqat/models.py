"""
نماذج الحلقات والجلسات
Halaqa (Circle) and Session Models for Tartil
"""
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


class Course(models.Model):
    """نموذج المسار/الدورة"""

    class CourseType(models.TextChoices):
        HIFZ = 'hifz', _('حفظ')
        MURAJA = 'muraja', _('مراجعة')
        TAJWEED = 'tajweed', _('تجويد')
        TILAWA = 'tilawa', _('تلاوة')
        IJAZAH = 'ijazah', _('إجازة')

    name = models.CharField(_('اسم المسار'), max_length=200)
    description = models.TextField(_('الوصف'), blank=True)
    course_type = models.CharField(
        _('نوع المسار'),
        max_length=20,
        choices=CourseType.choices,
        default=CourseType.HIFZ
    )
    duration_months = models.PositiveIntegerField(_('المدة بالأشهر'), default=12)
    price = models.DecimalField(_('السعر'), max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(_('نشط'), default=True)
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    image = models.ImageField(_('الصورة'), upload_to='courses/', blank=True, null=True)

    class Meta:
        verbose_name = _('مسار')
        verbose_name_plural = _('المسارات')
        ordering = ['name']

    def __str__(self):
        return self.name


class Halaqa(models.Model):
    """نموذج الحلقة"""

    class DayOfWeek(models.TextChoices):
        SATURDAY = 'sat', _('السبت')
        SUNDAY = 'sun', _('الأحد')
        MONDAY = 'mon', _('الإثنين')
        TUESDAY = 'tue', _('الثلاثاء')
        WEDNESDAY = 'wed', _('الأربعاء')
        THURSDAY = 'thu', _('الخميس')
        FRIDAY = 'fri', _('الجمعة')

    class HalaqaStatus(models.TextChoices):
        ACTIVE = 'active', _('نشطة')
        PAUSED = 'paused', _('متوقفة')
        COMPLETED = 'completed', _('مكتملة')
        CANCELLED = 'cancelled', _('ملغاة')

    name = models.CharField(_('اسم الحلقة'), max_length=200)
    course = models.ForeignKey(
        Course,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='halaqat',
        verbose_name=_('المسار')
    )
    sheikh = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='taught_halaqat',
        limit_choices_to={'user_type': 'sheikh'},
        verbose_name=_('الشيخ')
    )
    description = models.TextField(_('الوصف'), blank=True)
    max_students = models.PositiveIntegerField(_('الحد الأقصى للطلاب'), default=10)
    schedule_days = models.CharField(_('أيام الحلقة'), max_length=100, blank=True)
    schedule_time = models.TimeField(_('وقت الحلقة'), null=True, blank=True)
    duration_minutes = models.PositiveIntegerField(_('مدة الجلسة بالدقائق'), default=30)
    meet_link = models.URLField(_('رابط Google Meet'), blank=True)
    status = models.CharField(
        _('الحالة'),
        max_length=20,
        choices=HalaqaStatus.choices,
        default=HalaqaStatus.ACTIVE
    )
    is_private = models.BooleanField(_('حلقة خاصة'), default=False)
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    updated_at = models.DateTimeField(_('تاريخ التحديث'), auto_now=True)

    class Meta:
        verbose_name = _('حلقة')
        verbose_name_plural = _('الحلقات')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.sheikh.get_full_name()}"

    @property
    def enrolled_count(self):
        return self.enrollments.filter(status='active').count()

    @property
    def is_full(self):
        return self.enrolled_count >= self.max_students

    @property
    def available_spots(self):
        return max(0, self.max_students - self.enrolled_count)


class HalaqaEnrollment(models.Model):
    """نموذج تسجيل الطالب في الحلقة"""

    class EnrollmentStatus(models.TextChoices):
        PENDING = 'pending', _('قيد الانتظار')
        ACTIVE = 'active', _('نشط')
        COMPLETED = 'completed', _('مكتمل')
        WITHDRAWN = 'withdrawn', _('منسحب')
        SUSPENDED = 'suspended', _('موقوف')

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='halaqa_enrollments',
        limit_choices_to={'user_type': 'student'},
        verbose_name=_('الطالب')
    )
    halaqa = models.ForeignKey(
        Halaqa,
        on_delete=models.CASCADE,
        related_name='enrollments',
        verbose_name=_('الحلقة')
    )
    enrolled_date = models.DateField(_('تاريخ التسجيل'), auto_now_add=True)
    status = models.CharField(
        _('الحالة'),
        max_length=20,
        choices=EnrollmentStatus.choices,
        default=EnrollmentStatus.ACTIVE
    )
    notes = models.TextField(_('ملاحظات'), blank=True)

    class Meta:
        verbose_name = _('تسجيل في حلقة')
        verbose_name_plural = _('تسجيلات الحلقات')
        unique_together = ['student', 'halaqa']
        ordering = ['-enrolled_date']

    def __str__(self):
        return f"{self.student.get_full_name()} - {self.halaqa.name}"


class Session(models.Model):
    """نموذج الجلسة"""

    class SessionStatus(models.TextChoices):
        SCHEDULED = 'scheduled', _('مجدولة')
        IN_PROGRESS = 'in_progress', _('جارية')
        COMPLETED = 'completed', _('مكتملة')
        CANCELLED = 'cancelled', _('ملغاة')
        POSTPONED = 'postponed', _('مؤجلة')

    halaqa = models.ForeignKey(
        Halaqa,
        on_delete=models.CASCADE,
        related_name='sessions',
        verbose_name=_('الحلقة')
    )
    date = models.DateField(_('التاريخ'))
    start_time = models.TimeField(_('وقت البدء'))
    end_time = models.TimeField(_('وقت الانتهاء'), null=True, blank=True)
    actual_start = models.DateTimeField(_('وقت البدء الفعلي'), null=True, blank=True)
    actual_end = models.DateTimeField(_('وقت الانتهاء الفعلي'), null=True, blank=True)
    meet_link = models.URLField(_('رابط الاجتماع'), blank=True)
    status = models.CharField(
        _('الحالة'),
        max_length=20,
        choices=SessionStatus.choices,
        default=SessionStatus.SCHEDULED
    )
    notes = models.TextField(_('ملاحظات'), blank=True)
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)

    class Meta:
        verbose_name = _('جلسة')
        verbose_name_plural = _('الجلسات')
        ordering = ['-date', '-start_time']

    def __str__(self):
        return f"{self.halaqa.name} - {self.date}"

    @property
    def duration_actual(self):
        """مدة الجلسة الفعلية بالدقائق"""
        if self.actual_start and self.actual_end:
            delta = self.actual_end - self.actual_start
            return int(delta.total_seconds() / 60)
        return 0

    def start_session(self):
        """بدء الجلسة"""
        self.status = self.SessionStatus.IN_PROGRESS
        self.actual_start = timezone.now()
        self.save()

    def end_session(self):
        """إنهاء الجلسة"""
        self.status = self.SessionStatus.COMPLETED
        self.actual_end = timezone.now()
        self.save()


class Attendance(models.Model):
    """نموذج الحضور"""

    class AttendanceStatus(models.TextChoices):
        PRESENT = 'present', _('حاضر')
        ABSENT = 'absent', _('غائب')
        EXCUSED = 'excused', _('معذور')
        LATE = 'late', _('متأخر')

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='attendances',
        verbose_name=_('الطالب')
    )
    session = models.ForeignKey(
        Session,
        on_delete=models.CASCADE,
        related_name='attendances',
        verbose_name=_('الجلسة')
    )
    status = models.CharField(
        _('الحالة'),
        max_length=20,
        choices=AttendanceStatus.choices,
        default=AttendanceStatus.PRESENT
    )
    check_in_time = models.DateTimeField(_('وقت الدخول'), null=True, blank=True)
    check_out_time = models.DateTimeField(_('وقت الخروج'), null=True, blank=True)
    notes = models.TextField(_('ملاحظات'), blank=True)

    class Meta:
        verbose_name = _('حضور')
        verbose_name_plural = _('سجل الحضور')
        unique_together = ['student', 'session']

    def __str__(self):
        return f"{self.student.get_full_name()} - {self.session.date} - {self.get_status_display()}"
