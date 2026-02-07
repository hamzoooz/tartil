"""
نماذج المقررات والدورات الدراسية
Courses and Curriculum Models for Tartil
"""
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator


class Curriculum(models.Model):
    """نموذج المنهج/المقرر الدراسي"""
    
    class CurriculumType(models.TextChoices):
        HIFZ = 'hifz', _('حفظ')
        TAJWEED = 'tajweed', _('تجويد')
        TAFSEER = 'tafseer', _('تفسير')
        TAJWEED_TAFSEER = 'tajweed_tafseer', _('تجويد وتفسير')
        COMPREHENSIVE = 'comprehensive', _('شامل')
    
    name = models.CharField(_('اسم المقرر'), max_length=200)
    description = models.TextField(_('الوصف'), blank=True)
    curriculum_type = models.CharField(
        _('نوع المقرر'),
        max_length=20,
        choices=CurriculumType.choices,
        default=CurriculumType.HIFZ
    )
    image = models.ImageField(_('صورة المقرر'), upload_to='curriculum/', blank=True, null=True)
    
    # المحتوى
    target_surah_from = models.ForeignKey(
        'quran.Surah',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='curriculum_starts',
        verbose_name=_('من سورة')
    )
    target_surah_to = models.ForeignKey(
        'quran.Surah',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='curriculum_ends',
        verbose_name=_('إلى سورة')
    )
    target_juz_from = models.PositiveIntegerField(_('من جزء'), default=1, validators=[MinValueValidator(1), MaxValueValidator(30)])
    target_juz_to = models.PositiveIntegerField(_('إلى جزء'), default=30, validators=[MinValueValidator(1), MaxValueValidator(30)])
    
    # المدة والتنظيم
    duration_weeks = models.PositiveIntegerField(_('المدة بالأسابيع'), default=12)
    lessons_per_week = models.PositiveIntegerField(_('الدروس أسبوعياً'), default=2)
    minutes_per_lesson = models.PositiveIntegerField(_('دقيقة للدرس'), default=60)
    
    is_active = models.BooleanField(_('نشط'), default=True)
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    updated_at = models.DateTimeField(_('تاريخ التحديث'), auto_now=True)
    
    class Meta:
        verbose_name = _('مقرر دراسي')
        verbose_name_plural = _('المقررات الدراسية')
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    @property
    def total_lessons(self):
        """إجمالي عدد الدروس"""
        return self.duration_weeks * self.lessons_per_week
    
    @property
    def target_juz_count(self):
        """عدد الأجزاء المستهدفة"""
        return self.target_juz_to - self.target_juz_from + 1


class CurriculumLesson(models.Model):
    """نموذج درس المقرر"""
    
    class LessonType(models.TextChoices):
        HIFZ = 'hifz', _('حفظ')
        MURAJA = 'muraja', _('مراجعة')
        TAJWEED = 'tajweed', _('تجويد')
        TAFSEER = 'tafseer', _('تفسير')
        TEST = 'test', _('اختبار')
        REVISION = 'revision', _('مراجعة عامة')
    
    curriculum = models.ForeignKey(
        Curriculum,
        on_delete=models.CASCADE,
        related_name='lessons',
        verbose_name=_('المقرر')
    )
    lesson_number = models.PositiveIntegerField(_('رقم الدرس'))
    title = models.CharField(_('عنوان الدرس'), max_length=200)
    description = models.TextField(_('وصف الدرس'), blank=True)
    lesson_type = models.CharField(
        _('نوع الدرس'),
        max_length=20,
        choices=LessonType.choices,
        default=LessonType.HIFZ
    )
    
    # المحتوى القرآني
    surah_from = models.ForeignKey(
        'quran.Surah',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lesson_starts',
        verbose_name=_('من سورة')
    )
    ayah_from = models.PositiveIntegerField(_('من آية'), default=1)
    surah_to = models.ForeignKey(
        'quran.Surah',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lesson_ends',
        verbose_name=_('إلى سورة')
    )
    ayah_to = models.PositiveIntegerField(_('إلى آية'), default=1)
    
    # التفسير
    tafseer_content = models.TextField(_('محتوى التفسير'), blank=True)
    tafseer_video_url = models.URLField(_('رابط فيديو التفسير'), blank=True)
    
    # المدة
    duration_minutes = models.PositiveIntegerField(_('مدة الدرس'), default=60)
    
    # الأسبقية
    prerequisite_lessons = models.ManyToManyField(
        'self',
        blank=True,
        symmetrical=False,
        related_name='required_for',
        verbose_name=_('الدروس المسبقة')
    )
    
    is_active = models.BooleanField(_('نشط'), default=True)
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('درس المقرر')
        verbose_name_plural = _('دروس المقرر')
        ordering = ['curriculum', 'lesson_number']
        unique_together = ['curriculum', 'lesson_number']
    
    def __str__(self):
        return f"{self.curriculum.name} - الدرس {self.lesson_number}: {self.title}"


class StudentCurriculum(models.Model):
    """نموذج تسجيل الطالب في المقرر"""
    
    class Status(models.TextChoices):
        NOT_STARTED = 'not_started', _('لم يبدأ')
        IN_PROGRESS = 'in_progress', _('جاري')
        COMPLETED = 'completed', _('مكتمل')
        ON_HOLD = 'on_hold', _('متوقف')
    
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='enrolled_curriculums',
        limit_choices_to={'user_type': 'student'},
        verbose_name=_('الطالب')
    )
    curriculum = models.ForeignKey(
        Curriculum,
        on_delete=models.CASCADE,
        related_name='enrolled_students',
        verbose_name=_('المقرر')
    )
    sheikh = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='supervised_curriculums',
        limit_choices_to={'user_type': 'sheikh'},
        verbose_name=_('الشيخ المشرف')
    )
    
    status = models.CharField(
        _('الحالة'),
        max_length=20,
        choices=Status.choices,
        default=Status.NOT_STARTED
    )
    current_lesson = models.ForeignKey(
        CurriculumLesson,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('الدرس الحالي')
    )
    
    # التواريخ
    start_date = models.DateField(_('تاريخ البدء'), null=True, blank=True)
    expected_end_date = models.DateField(_('تاريخ الانتهاء المتوقع'), null=True, blank=True)
    actual_end_date = models.DateField(_('تاريخ الانتهاء الفعلي'), null=True, blank=True)
    
    # التنبيهات
    enable_reminders = models.BooleanField(_('تفعيل التنبيهات'), default=True)
    reminder_time = models.TimeField(_('وقت التنبيه'), default='10:00')
    timezone = models.CharField(_('المنطقة الزمنية'), max_length=50, default='Asia/Riyadh')
    
    created_at = models.DateTimeField(_('تاريخ التسجيل'), auto_now_add=True)
    updated_at = models.DateTimeField(_('تاريخ التحديث'), auto_now=True)
    
    class Meta:
        verbose_name = _('مقرر طالب')
        verbose_name_plural = _('مقررات الطلاب')
        unique_together = ['student', 'curriculum']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.curriculum.name}"
    
    def get_progress_percentage(self):
        """نسبة التقدم في المقرر"""
        if not self.current_lesson:
            return 0
        total_lessons = self.curriculum.lessons.count()
        if total_lessons == 0:
            return 0
        return int((self.current_lesson.lesson_number / total_lessons) * 100)


class MotivationalQuote(models.Model):
    """نموذج الكلمات التحفيزية"""
    
    class QuoteCategory(models.TextChoices):
        GENERAL = 'general', _('عام')
        RAMADAN = 'ramadan', _('رمضان')
        MORNING = 'morning', _('صباحية')
        EVENING = 'evening', _('مسائية')
        FRIDAY = 'friday', _('يوم الجمعة')
        ACHIEVEMENT = 'achievement', _('إنجاز')
        ENCOURAGEMENT = 'encouragement', _('تشجيع')
    
    title = models.CharField(_('العنوان'), max_length=200)
    content = models.TextField(_('المحتوى'))
    category = models.CharField(
        _('التصنيف'),
        max_length=20,
        choices=QuoteCategory.choices,
        default=QuoteCategory.GENERAL
    )
    
    # مصدر الاقتباس
    author = models.CharField(_('القائل'), max_length=100, blank=True)
    source = models.CharField(_('المصدر'), max_length=200, blank=True)
    
    # الوسائط
    image = models.ImageField(_('صورة'), upload_to='quotes/', blank=True, null=True)
    audio = models.FileField(_('ملف صوتي'), upload_to='quotes/audio/', blank=True, null=True)
    
    # الجدولة
    is_scheduled = models.BooleanField(_('مجدول'), default=False)
    scheduled_date = models.DateField(_('تاريخ النشر'), null=True, blank=True)
    scheduled_time = models.TimeField(_('وقت النشر'), null=True, blank=True)
    timezone = models.CharField(_('المنطقة الزمنية'), max_length=50, default='Asia/Riyadh')
    
    # التكرار
    is_recurring = models.BooleanField(_('متكرر'), default=False)
    recurring_days = models.JSONField(_('أيام التكرار'), default=list, blank=True)  # [0, 1, 2] للأحد، الاثنين، الثلاثاء
    
    # الحالة
    is_published = models.BooleanField(_('منشور'), default=False)
    published_at = models.DateTimeField(_('تاريخ النشر الفعلي'), null=True, blank=True)
    
    # الإحصائيات
    view_count = models.PositiveIntegerField(_('عدد المشاهدات'), default=0)
    
    is_active = models.BooleanField(_('نشط'), default=True)
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_quotes',
        verbose_name=_('أنشئ بواسطة')
    )
    
    class Meta:
        verbose_name = _('كلمة تحفيزية')
        verbose_name_plural = _('الكلمات التحفيزية')
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def publish(self):
        """نشر الكلمة"""
        self.is_published = True
        self.published_at = timezone.now()
        self.save()


class QuoteNotification(models.Model):
    """نموذج إشعارات الكلمات التحفيزية"""
    
    quote = models.ForeignKey(
        MotivationalQuote,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name=_('الكلمة التحفيزية')
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='quote_notifications',
        verbose_name=_('الطالب')
    )
    is_read = models.BooleanField(_('مقروء'), default=False)
    read_at = models.DateTimeField(_('تاريخ القراءة'), null=True, blank=True)
    created_at = models.DateTimeField(_('تاريخ الإرسال'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('إشعار تحفيزي')
        verbose_name_plural = _('إشعارات تحفيزية')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.quote.title}"


class TafseerLesson(models.Model):
    """نموذج درس التفسير"""
    
    surah = models.ForeignKey(
        'quran.Surah',
        on_delete=models.CASCADE,
        related_name='tafseer_lessons',
        verbose_name=_('السورة')
    )
    ayah_from = models.PositiveIntegerField(_('من آية'), default=1)
    ayah_to = models.PositiveIntegerField(_('إلى آية'))
    
    title = models.CharField(_('عنوان الدرس'), max_length=200)
    content = models.TextField(_('محتوى الدرس'))
    summary = models.TextField(_('ملخص الدرس'), blank=True)
    
    # الوسائط
    video_url = models.URLField(_('رابط الفيديو'), blank=True)
    audio_url = models.URLField(_('رابط الصوت'), blank=True)
    pdf_file = models.FileField(_('ملف PDF'), upload_to='tafseer/pdf/', blank=True, null=True)
    
    # الجدولة
    is_scheduled = models.BooleanField(_('مجدول'), default=False)
    scheduled_date = models.DateField(_('تاريخ الجدولة'), null=True, blank=True)
    scheduled_time = models.TimeField(_('وقت الجدولة'), null=True, blank=True)
    timezone = models.CharField(_('المنطقة الزمنية'), max_length=50, default='Asia/Riyadh')
    
    # التكرار
    is_recurring = models.BooleanField(_('متكرر'), default=False)
    recurring_type = models.CharField(
        _('نوع التكرار'),
        max_length=20,
        choices=[
            ('daily', _('يومي')),
            ('weekly', _('أسبوعي')),
            ('monthly', _('شهري')),
            ('ramadan', _('رمضان')),
        ],
        default='weekly'
    )
    
    # الحالة
    is_published = models.BooleanField(_('منشور'), default=False)
    published_at = models.DateTimeField(_('تاريخ النشر'), null=True, blank=True)
    
    # المجموعة المستهدفة
    target_halaqat = models.ManyToManyField(
        'halaqat.Halaqa',
        blank=True,
        related_name='scheduled_tafseer',
        verbose_name=_('الحلقات المستهدفة')
    )
    target_curriculums = models.ManyToManyField(
        Curriculum,
        blank=True,
        related_name='tafseer_lessons',
        verbose_name=_('المقررات المستهدفة')
    )
    
    # الإحصائيات
    view_count = models.PositiveIntegerField(_('عدد المشاهدات'), default=0)
    
    is_active = models.BooleanField(_('نشط'), default=True)
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_tafseer',
        verbose_name=_('أنشئ بواسطة')
    )
    
    class Meta:
        verbose_name = _('درس تفسير')
        verbose_name_plural = _('دروس التفسير')
        ordering = ['surah__number', 'ayah_from']
    
    def __str__(self):
        return f"{self.surah.name_arabic} ({self.ayah_from}-{self.ayah_to}): {self.title}"
    
    def publish(self):
        """نشر الدرس"""
        self.is_published = True
        self.published_at = timezone.now()
        self.save()


class ScheduledNotification(models.Model):
    """نموذج الإشعارات المجدولة"""
    
    class NotificationType(models.TextChoices):
        QUOTE = 'quote', _('كلمة تحفيزية')
        TAFSEER = 'tafseer', _('درس تفسير')
        REMINDER = 'reminder', _('تذكير')
        LESSON = 'lesson', _('درس')
        CUSTOM = 'custom', _('مخصص')
    
    class Status(models.TextChoices):
        PENDING = 'pending', _('معلق')
        SENT = 'sent', _('تم الإرسال')
        FAILED = 'failed', _('فشل')
        CANCELLED = 'cancelled', _('ملغي')
    
    title = models.CharField(_('العنوان'), max_length=200)
    content = models.TextField(_('المحتوى'))
    notification_type = models.CharField(
        _('نوع الإشعار'),
        max_length=20,
        choices=NotificationType.choices,
        default=NotificationType.CUSTOM
    )
    
    # الربط بالمحتوى
    quote = models.ForeignKey(
        MotivationalQuote,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='scheduled_notifications',
        verbose_name=_('الكلمة التحفيزية')
    )
    tafseer = models.ForeignKey(
        TafseerLesson,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='scheduled_notifications',
        verbose_name=_('درس التفسير')
    )
    
    # الجدولة
    scheduled_datetime = models.DateTimeField(_('تاريخ ووقت الإرسال'))
    timezone = models.CharField(_('المنطقة الزمنية'), max_length=50, default='Asia/Riyadh')
    
    # المستهدفون
    target_all_students = models.BooleanField(_('جميع الطلاب'), default=False)
    target_halaqat = models.ManyToManyField(
        'halaqat.Halaqa',
        blank=True,
        related_name='scheduled_notifications',
        verbose_name=_('الحلقات المستهدفة')
    )
    target_students = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='targeted_notifications',
        limit_choices_to={'user_type': 'student'},
        verbose_name=_('طلاب محددون')
    )
    
    # الحالة
    status = models.CharField(
        _('الحالة'),
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    sent_at = models.DateTimeField(_('تاريخ الإرسال الفعلي'), null=True, blank=True)
    error_message = models.TextField(_('رسالة الخطأ'), blank=True)
    
    # التكرار
    is_recurring = models.BooleanField(_('متكرر'), default=False)
    recurring_cron = models.CharField(_('تعبير Cron'), max_length=100, blank=True, help_text='مثال: 0 10 * * * للساعة 10 صباحاً يومياً')
    
    is_active = models.BooleanField(_('نشط'), default=True)
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_scheduled_notifications',
        verbose_name=_('أنشئ بواسطة')
    )
    
    class Meta:
        verbose_name = _('إشعار مجدول')
        verbose_name_plural = _('الإشعارات المجدولة')
        ordering = ['scheduled_datetime']
    
    def __str__(self):
        return f"{self.title} - {self.scheduled_datetime}"
    
    def mark_as_sent(self):
        """تحديث حالة الإشعار إلى تم الإرسال"""
        self.status = self.Status.SENT
        self.sent_at = timezone.now()
        self.save()
    
    def mark_as_failed(self, error):
        """تحديث حالة الإشعار إلى فشل"""
        self.status = self.Status.FAILED
        self.error_message = str(error)
        self.save()


class LessonReminder(models.Model):
    """نموذج تذكير الدروس"""
    
    student_curriculum = models.ForeignKey(
        StudentCurriculum,
        on_delete=models.CASCADE,
        related_name='reminders',
        verbose_name=_('مقرر الطالب')
    )
    lesson = models.ForeignKey(
        CurriculumLesson,
        on_delete=models.CASCADE,
        related_name='reminders',
        verbose_name=_('الدرس')
    )
    
    # التاريخ المجدول
    scheduled_date = models.DateField(_('تاريخ الدرس'))
    scheduled_time = models.TimeField(_('وقت الدرس'))
    
    # التذكيرات
    remind_before_minutes = models.PositiveIntegerField(_('تذكير قبل (دقيقة)'), default=60)
    reminder_sent = models.BooleanField(_('تم إرسال التذكير'), default=False)
    reminder_sent_at = models.DateTimeField(_('تاريخ إرسال التذكير'), null=True, blank=True)
    
    # الحالة
    is_completed = models.BooleanField(_('مكتمل'), default=False)
    completed_at = models.DateTimeField(_('تاريخ الإكمال'), null=True, blank=True)
    
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('تذكير درس')
        verbose_name_plural = _('تذكيرات الدروس')
        ordering = ['scheduled_date', 'scheduled_time']
    
    def __str__(self):
        return f"{self.student_curriculum.student.get_full_name()} - {self.lesson.title} - {self.scheduled_date}"
    
    def send_reminder(self):
        """إرسال التذكير"""
        self.reminder_sent = True
        self.reminder_sent_at = timezone.now()
        self.save()
    
    def mark_completed(self):
        """تحديد الدرس كمكتمل"""
        self.is_completed = True
        self.completed_at = timezone.now()
        self.save()
