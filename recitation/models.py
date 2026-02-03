"""
نماذج التسميع والتقييم
Recitation and Evaluation Models for Tartil
"""
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator


class RecitationRecord(models.Model):
    """نموذج سجل التسميع"""

    class RecitationType(models.TextChoices):
        NEW = 'new', _('حفظ جديد')
        REVIEW = 'review', _('مراجعة')
        TILAWA = 'tilawa', _('تلاوة')

    class GradeLevel(models.TextChoices):
        EXCELLENT = 'excellent', _('ممتاز')
        VERY_GOOD = 'very_good', _('جيد جداً')
        GOOD = 'good', _('جيد')
        ACCEPTABLE = 'acceptable', _('مقبول')
        WEAK = 'weak', _('ضعيف')

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='recitation_records',
        verbose_name=_('الطالب')
    )
    session = models.ForeignKey(
        'halaqat.Session',
        on_delete=models.CASCADE,
        related_name='recitation_records',
        verbose_name=_('الجلسة')
    )
    surah_start = models.ForeignKey(
        'quran.Surah',
        on_delete=models.CASCADE,
        related_name='recitation_starts',
        verbose_name=_('سورة البداية')
    )
    ayah_start = models.PositiveIntegerField(_('آية البداية'))
    surah_end = models.ForeignKey(
        'quran.Surah',
        on_delete=models.CASCADE,
        related_name='recitation_ends',
        verbose_name=_('سورة النهاية')
    )
    ayah_end = models.PositiveIntegerField(_('آية النهاية'))
    recitation_type = models.CharField(
        _('نوع التسميع'),
        max_length=20,
        choices=RecitationType.choices,
        default=RecitationType.NEW
    )
    grade = models.DecimalField(
        _('الدرجة'),
        max_digits=4,
        decimal_places=1,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        default=0
    )
    grade_level = models.CharField(
        _('مستوى التقييم'),
        max_length=20,
        choices=GradeLevel.choices,
        blank=True
    )
    total_errors = models.PositiveIntegerField(_('إجمالي الأخطاء'), default=0)
    duration_minutes = models.PositiveIntegerField(_('المدة بالدقائق'), default=0)
    notes = models.TextField(_('ملاحظات الشيخ'), blank=True)
    sheikh_feedback = models.TextField(_('تعليق الشيخ'), blank=True)
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    updated_at = models.DateTimeField(_('تاريخ التحديث'), auto_now=True)

    class Meta:
        verbose_name = _('سجل تسميع')
        verbose_name_plural = _('سجلات التسميع')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student.get_full_name()} - {self.surah_start.name_arabic}"

    def save(self, *args, **kwargs):
        # تحديد مستوى التقييم بناءً على الدرجة
        if self.grade >= 90:
            self.grade_level = self.GradeLevel.EXCELLENT
        elif self.grade >= 80:
            self.grade_level = self.GradeLevel.VERY_GOOD
        elif self.grade >= 70:
            self.grade_level = self.GradeLevel.GOOD
        elif self.grade >= 60:
            self.grade_level = self.GradeLevel.ACCEPTABLE
        else:
            self.grade_level = self.GradeLevel.WEAK
        super().save(*args, **kwargs)

    @property
    def pages_count(self):
        """عدد الصفحات المسمعة (تقريبي)"""
        # حساب تقريبي للصفحات
        return 1

    @property
    def lines_count(self):
        """عدد الأسطر المسمعة (تقريبي)"""
        return 15


class RecitationError(models.Model):
    """نموذج الأخطاء في التسميع"""

    class ErrorType(models.TextChoices):
        TAJWEED = 'tajweed', _('خطأ تجويد')
        TASHKEEL = 'tashkeel', _('خطأ تشكيل')
        FORGET = 'forget', _('نسيان')
        ADDITION = 'addition', _('إضافة')
        REPLACEMENT = 'replacement', _('إبدال')
        HESITATION = 'hesitation', _('تردد')
        PRONUNCIATION = 'pronunciation', _('نطق')

    class ErrorSeverity(models.TextChoices):
        MINOR = 'minor', _('بسيط')
        MAJOR = 'major', _('جسيم')
        CRITICAL = 'critical', _('خطير')

    record = models.ForeignKey(
        RecitationRecord,
        on_delete=models.CASCADE,
        related_name='errors',
        verbose_name=_('سجل التسميع')
    )
    surah = models.ForeignKey(
        'quran.Surah',
        on_delete=models.CASCADE,
        verbose_name=_('السورة')
    )
    ayah = models.PositiveIntegerField(_('رقم الآية'))
    word_index = models.PositiveIntegerField(_('ترتيب الكلمة'), default=0)
    word_text = models.CharField(_('نص الكلمة'), max_length=100, blank=True)
    error_type = models.CharField(
        _('نوع الخطأ'),
        max_length=20,
        choices=ErrorType.choices
    )
    severity = models.CharField(
        _('شدة الخطأ'),
        max_length=20,
        choices=ErrorSeverity.choices,
        default=ErrorSeverity.MINOR
    )
    notes = models.TextField(_('ملاحظات'), blank=True)
    created_at = models.DateTimeField(_('تاريخ التسجيل'), auto_now_add=True)

    class Meta:
        verbose_name = _('خطأ تسميع')
        verbose_name_plural = _('أخطاء التسميع')
        ordering = ['surah', 'ayah', 'word_index']

    def __str__(self):
        return f"{self.surah.name_arabic} ({self.ayah}) - {self.get_error_type_display()}"


class MemorizationProgress(models.Model):
    """نموذج تتبع تقدم الحفظ"""

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='memorization_progress',
        verbose_name=_('الطالب')
    )
    surah = models.ForeignKey(
        'quran.Surah',
        on_delete=models.CASCADE,
        verbose_name=_('السورة')
    )
    ayah_from = models.PositiveIntegerField(_('من آية'), default=1)
    ayah_to = models.PositiveIntegerField(_('إلى آية'))
    is_memorized = models.BooleanField(_('تم الحفظ'), default=False)
    is_reviewed = models.BooleanField(_('تمت المراجعة'), default=False)
    last_review_date = models.DateField(_('تاريخ آخر مراجعة'), null=True, blank=True)
    review_count = models.PositiveIntegerField(_('عدد المراجعات'), default=0)
    average_grade = models.DecimalField(
        _('متوسط الدرجة'),
        max_digits=4,
        decimal_places=1,
        default=0
    )
    notes = models.TextField(_('ملاحظات'), blank=True)
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    updated_at = models.DateTimeField(_('تاريخ التحديث'), auto_now=True)

    class Meta:
        verbose_name = _('تقدم حفظ')
        verbose_name_plural = _('تقدم الحفظ')
        unique_together = ['student', 'surah', 'ayah_from', 'ayah_to']

    def __str__(self):
        return f"{self.student.get_full_name()} - {self.surah.name_arabic}"


class DailyGoal(models.Model):
    """نموذج الأهداف اليومية"""

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='daily_goals',
        verbose_name=_('الطالب')
    )
    date = models.DateField(_('التاريخ'))
    target_new_lines = models.PositiveIntegerField(_('أسطر الحفظ المستهدفة'), default=5)
    actual_new_lines = models.PositiveIntegerField(_('أسطر الحفظ الفعلية'), default=0)
    target_review_pages = models.PositiveIntegerField(_('صفحات المراجعة المستهدفة'), default=2)
    actual_review_pages = models.PositiveIntegerField(_('صفحات المراجعة الفعلية'), default=0)
    is_achieved = models.BooleanField(_('تم تحقيق الهدف'), default=False)
    notes = models.TextField(_('ملاحظات'), blank=True)

    class Meta:
        verbose_name = _('هدف يومي')
        verbose_name_plural = _('الأهداف اليومية')
        unique_together = ['student', 'date']
        ordering = ['-date']

    def __str__(self):
        return f"{self.student.get_full_name()} - {self.date}"

    def check_achievement(self):
        """التحقق من تحقيق الهدف"""
        self.is_achieved = (
            self.actual_new_lines >= self.target_new_lines and
            self.actual_review_pages >= self.target_review_pages
        )
        self.save()
