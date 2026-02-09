"""
نماذج المستخدمين
User Models for Tartil
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class CustomUser(AbstractUser):
    """نموذج المستخدم المخصص"""

    class UserType(models.TextChoices):
        ADMIN = 'admin', _('مدير')
        SHEIKH = 'sheikh', _('شيخ')
        STUDENT = 'student', _('طالب')
        PARENT = 'parent', _('ولي أمر')

    class Gender(models.TextChoices):
        MALE = 'male', _('ذكر')
        FEMALE = 'female', _('أنثى')

    user_type = models.CharField(
        _('نوع المستخدم'),
        max_length=10,
        choices=UserType.choices,
        default=UserType.STUDENT
    )
    phone = models.CharField(_('رقم الجوال'), max_length=20, blank=True)
    profile_image = models.ImageField(
        _('الصورة الشخصية'),
        upload_to='profiles/',
        blank=True,
        null=True
    )
    gender = models.CharField(
        _('الجنس'),
        max_length=10,
        choices=Gender.choices,
        blank=True
    )
    bio = models.TextField(_('نبذة'), blank=True)
    date_of_birth = models.DateField(_('تاريخ الميلاد'), null=True, blank=True)
    country = models.CharField(_('الدولة'), max_length=100, blank=True)
    city = models.CharField(_('المدينة'), max_length=100, blank=True)
    is_active_member = models.BooleanField(_('عضو نشط'), default=True)

    class Meta:
        verbose_name = _('مستخدم')
        verbose_name_plural = _('المستخدمون')

    def __str__(self):
        return self.get_full_name() or self.username

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def is_admin(self):
        return self.user_type == self.UserType.ADMIN

    @property
    def is_sheikh(self):
        return self.user_type == self.UserType.SHEIKH

    @property
    def is_student(self):
        return self.user_type == self.UserType.STUDENT

    @property
    def is_parent(self):
        return self.user_type == self.UserType.PARENT


class StudentProfile(models.Model):
    """ملف الطالب التفصيلي"""

    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='student_profile',
        verbose_name=_('المستخدم')
    )
    parent = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children',
        limit_choices_to={'user_type': 'parent'},
        verbose_name=_('ولي الأمر')
    )
    current_surah = models.PositiveIntegerField(_('السورة الحالية'), default=1)
    current_ayah = models.PositiveIntegerField(_('الآية الحالية'), default=1)
    total_memorized_pages = models.PositiveIntegerField(_('إجمالي الصفحات المحفوظة'), default=0)
    total_memorized_juz = models.PositiveIntegerField(_('إجمالي الأجزاء المحفوظة'), default=0)
    memorization_start_date = models.DateField(_('تاريخ بدء الحفظ'), null=True, blank=True)
    target_completion_date = models.DateField(_('تاريخ الإتمام المستهدف'), null=True, blank=True)
    notes = models.TextField(_('ملاحظات'), blank=True)
    total_points = models.PositiveIntegerField(_('إجمالي النقاط'), default=0)

    class Meta:
        verbose_name = _('ملف طالب')
        verbose_name_plural = _('ملفات الطلاب')

    def __str__(self):
        return f"ملف {self.user.get_full_name()}"

    @property
    def memorization_percentage(self):
        """نسبة الإتمام من المصحف (604 صفحة)"""
        return round((self.total_memorized_pages / 604) * 100, 1)


class SheikhProfile(models.Model):
    """ملف الشيخ/المعلم التفصيلي"""

    class Specialization(models.TextChoices):
        HIFZ = 'hifz', _('حفظ')
        TAJWEED = 'tajweed', _('تجويد')
        QIRAAT = 'qiraat', _('قراءات')
        IJAZAH = 'ijazah', _('إجازة')

    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='sheikh_profile',
        verbose_name=_('المستخدم')
    )
    specialization = models.CharField(
        _('التخصص'),
        max_length=20,
        choices=Specialization.choices,
        default=Specialization.HIFZ
    )
    ijazah_info = models.TextField(_('معلومات الإجازة'), blank=True)
    years_of_experience = models.PositiveIntegerField(_('سنوات الخبرة'), default=0)
    max_students = models.PositiveIntegerField(_('الحد الأقصى للطلاب'), default=20)
    available_days = models.CharField(_('أيام التوفر'), max_length=100, blank=True)
    available_times = models.TextField(_('أوقات التوفر'), blank=True)
    hourly_rate = models.DecimalField(
        _('الأجر بالساعة'),
        max_digits=10,
        decimal_places=2,
        default=0
    )
    rating = models.DecimalField(
        _('التقييم'),
        max_digits=3,
        decimal_places=2,
        default=0
    )
    total_sessions = models.PositiveIntegerField(_('إجمالي الجلسات'), default=0)

    class Meta:
        verbose_name = _('ملف شيخ')
        verbose_name_plural = _('ملفات المشايخ')

    def __str__(self):
        return f"الشيخ {self.user.get_full_name()}"


class Notification(models.Model):
    """نموذج الإشعارات"""

    class NotificationType(models.TextChoices):
        SESSION = 'session', _('جلسة')
        GRADE = 'grade', _('درجة')
        BADGE = 'badge', _('وسام')
        SYSTEM = 'system', _('نظام')
        REMINDER = 'reminder', _('تذكير')

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name=_('المستخدم')
    )
    notification_type = models.CharField(
        _('نوع الإشعار'),
        max_length=20,
        choices=NotificationType.choices,
        default=NotificationType.SYSTEM
    )
    title = models.CharField(_('العنوان'), max_length=200)
    message = models.TextField(_('الرسالة'))
    is_read = models.BooleanField(_('مقروء'), default=False)
    link = models.CharField(_('الرابط'), max_length=500, blank=True)
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)

    class Meta:
        verbose_name = _('إشعار')
        verbose_name_plural = _('الإشعارات')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.user.username}"


class ActivityLog(models.Model):
    """سجل النشاط"""

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='activities',
        verbose_name=_('المستخدم')
    )
    action = models.CharField(_('الإجراء'), max_length=200)
    details = models.TextField(_('التفاصيل'), blank=True)
    ip_address = models.GenericIPAddressField(_('عنوان IP'), null=True, blank=True)
    created_at = models.DateTimeField(_('التاريخ'), auto_now_add=True)

    class Meta:
        verbose_name = _('سجل نشاط')
        verbose_name_plural = _('سجلات النشاط')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.action}"
