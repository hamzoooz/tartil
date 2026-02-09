"""
نماذج نظام النشر والتنبيهات المجدول
Models for Smart Notification & Publishing System
"""
import uuid
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator


class NotificationTemplate(models.Model):
    """قالب الإشعارات - قابل لإعادة الاستخدام"""
    
    class ContentType(models.TextChoices):
        LESSON = 'lesson', _('درس اليوم')
        REMINDER = 'reminder', _('تذكير بالدرس')
        MORNING_MOTIVATION = 'morning_motivation', _('تحفيز صباحي')
        EVENING_REFLECTION = 'evening_reflection', _('تأمل مسائي')
        ENCOURAGEMENT = 'encouragement', _('رسائل تشجيعية')
        AWARENESS = 'awareness', _('رسائل توعوية')
        ANNOUNCEMENT = 'announcement', _('إعلان عام')
    
    name = models.CharField(_('اسم القالب'), max_length=200)
    content_type = models.CharField(
        _('نوع المحتوى'),
        max_length=30,
        choices=ContentType.choices
    )
    title_template = models.CharField(_('عنوان القالب'), max_length=200)
    message_template = models.TextField(_('نص القالب'))
    image = models.ImageField(_('صورة'), upload_to='notification_templates/', blank=True, null=True)
    link = models.URLField(_('رابط'), blank=True)
    
    # المتغيرات المتاحة في القالب
    available_variables = models.JSONField(
        _('المتغيرات المتاحة'),
        default=list,
        help_text=_('متغيرات مثل: {student_name}, {lesson_title}, {surah_name}')
    )
    
    is_active = models.BooleanField(_('نشط'), default=True)
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    updated_at = models.DateTimeField(_('تاريخ التحديث'), auto_now=True)
    
    class Meta:
        verbose_name = _('قالب إشعار')
        verbose_name_plural = _('قوالب الإشعارات')
        ordering = ['content_type', 'name']
    
    def __str__(self):
        return f"{self.get_content_type_display()} - {self.name}"


class ScheduledNotification(models.Model):
    """الإشعار المجدول - النموذج الرئيسي"""
    
    class Status(models.TextChoices):
        DRAFT = 'draft', _('مسودة')
        SCHEDULED = 'scheduled', _('مجدول')
        SENDING = 'sending', _('جاري الإرسال')
        SENT = 'sent', _('تم الإرسال')
        FAILED = 'failed', _('فشل')
        CANCELLED = 'cancelled', _('ملغي')
    
    class RecurrenceType(models.TextChoices):
        ONE_TIME = 'one_time', _('مرة واحدة')
        DAILY = 'daily', _('يومي')
        WEEKLY = 'weekly', _('أسبوعي')
        BIWEEKLY = 'biweekly', _('مرتين في الأسبوع')
        MONTHLY = 'monthly', _('شهري')
        CUSTOM = 'custom', _('مخصص')
    
    class TargetType(models.TextChoices):
        ALL_STUDENTS = 'all_students', _('جميع الطلاب')
        ALL_PARENTS = 'all_parents', _('جميع أولياء الأمور')
        ALL_TEACHERS = 'all_teachers', _('جميع المشايخ')
        HALAQA = 'halaqa', _('حلقة محددة')
        COURSE = 'course', _('مقرر محدد')
        SPECIFIC_USERS = 'specific_users', _('مستخدمين محددين')
    
    # المعلومات الأساسية
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(_('العنوان'), max_length=200)
    content_type = models.CharField(
        _('نوع المحتوى'),
        max_length=30,
        choices=NotificationTemplate.ContentType.choices
    )
    
    # ربط بالقالب (اختياري)
    template = models.ForeignKey(
        NotificationTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('القالب')
    )
    
    # المحتوى
    message = models.TextField(_('الرسالة'))
    image = models.ImageField(_('صورة'), upload_to='scheduled_notifications/', blank=True, null=True)
    link = models.URLField(_('رابط'), blank=True)
    
    # ربط بالدرس (اختياري - لأنواع الدروس)
    lesson = models.ForeignKey(
        'courses.CurriculumLesson',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('الدرس')
    )
    
    # ربط بالتفسير (اختياري)
    tafseer = models.ForeignKey(
        'courses.TafseerLesson',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('درس التفسير')
    )
    
    # الجدولة
    scheduled_datetime = models.DateTimeField(_('تاريخ ووقت الإرسال'))
    timezone = models.CharField(_('المنطقة الزمنية'), max_length=50, default='Asia/Riyadh')
    
    # التكرار
    recurrence_type = models.CharField(
        _('نوع التكرار'),
        max_length=20,
        choices=RecurrenceType.choices,
        default=RecurrenceType.ONE_TIME
    )
    recurrence_days = models.JSONField(
        _('أيام التكرار'),
        default=list,
        blank=True,
        help_text=_('للتكرار الأسبوعي: [0, 2, 4] للأحد، الثلاثاء، الخميس')
    )
    recurrence_end_date = models.DateField(_('تاريخ انتهاء التكرار'), null=True, blank=True)
    
    # المستهدفون
    target_type = models.CharField(
        _('نوع المستهدفين'),
        max_length=20,
        choices=TargetType.choices,
        default=TargetType.ALL_STUDENTS
    )
    target_halaqa = models.ForeignKey(
        'halaqat.Halaqa',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_('الحلقة المستهدفة')
    )
    target_course = models.ForeignKey(
        'courses.Curriculum',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_('المقرر المستهدف')
    )
    target_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='targeted_scheduled_notifications',
        verbose_name=_('المستخدمون المستهدفون')
    )
    
    # الحالة
    status = models.CharField(
        _('الحالة'),
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT
    )
    is_enabled = models.BooleanField(_('مفعّل'), default=True)
    
    # معلومات الأب
    parent_notification = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='child_notifications',
        verbose_name=_('الإشعار الأصلي')
    )
    
    # التتبع
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='ns_created_scheduled_notifications',
        verbose_name=_('أنشئ بواسطة')
    )
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    updated_at = models.DateTimeField(_('تاريخ التحديث'), auto_now=True)
    sent_at = models.DateTimeField(_('تاريخ الإرسال'), null=True, blank=True)
    sent_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ns_sent_scheduled_notifications',
        verbose_name=_('أُرسل بواسطة')
    )
    
    # الإحصائيات
    total_recipients = models.PositiveIntegerField(_('إجمالي المستلمين'), default=0)
    successful_sends = models.PositiveIntegerField(_('الإرسال الناجح'), default=0)
    failed_sends = models.PositiveIntegerField(_('الإرسال الفاشل'), default=0)
    
    class Meta:
        verbose_name = _('إشعار مجدول')
        verbose_name_plural = _('الإشعارات المجدولة')
        ordering = ['-scheduled_datetime']
        indexes = [
            models.Index(fields=['status', 'scheduled_datetime']),
            models.Index(fields=['content_type', 'status']),
            models.Index(fields=['is_enabled', 'status']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.scheduled_datetime.strftime('%Y-%m-%d %H:%M')}"
    
    def save(self, *args, **kwargs):
        # تحديث الحالة تلقائياً إذا كان الوقت قد مر
        if self.status == self.Status.SCHEDULED and self.scheduled_datetime < timezone.now():
            self.status = self.Status.FAILED
        super().save(*args, **kwargs)
    
    @property
    def is_overdue(self):
        """هل الإشعار متأخر؟"""
        return self.scheduled_datetime < timezone.now() and self.status == self.Status.SCHEDULED
    
    @property
    def can_send_now(self):
        """يمكن إرساله الآن؟"""
        return self.status in [self.Status.DRAFT, self.Status.SCHEDULED, self.Status.FAILED]


class NotificationDispatchLog(models.Model):
    """سجل إرسال الإشعارات - للتدقيق وإعادة المحاولة"""
    
    class Status(models.TextChoices):
        PENDING = 'pending', _('معلق')
        SUCCESS = 'success', _('نجاح')
        FAILED = 'failed', _('فشل')
        RETRYING = 'retrying', _('إعادة محاولة')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    notification = models.ForeignKey(
        ScheduledNotification,
        on_delete=models.CASCADE,
        related_name='dispatch_logs',
        verbose_name=_('الإشعار')
    )
    
    # معلومات المستلم
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_dispatch_logs',
        verbose_name=_('المستلم')
    )
    
    # معلومات الإرسال
    webhook_url = models.URLField(_('رابط Webhook'))
    payload = models.JSONField(_('البيانات المرسلة'))
    
    # الحالة والمحاولات
    status = models.CharField(
        _('الحالة'),
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    attempt_count = models.PositiveIntegerField(_('عدد المحاولات'), default=0)
    max_attempts = models.PositiveIntegerField(_('الحد الأقصى للمحاولات'), default=3)
    
    # النتائج
    response_status_code = models.PositiveIntegerField(_('رمز الاستجابة'), null=True, blank=True)
    response_body = models.TextField(_('نص الاستجابة'), blank=True)
    error_message = models.TextField(_('رسالة الخطأ'), blank=True)
    
    # التواريخ
    first_attempt_at = models.DateTimeField(_('أول محاولة'), null=True, blank=True)
    last_attempt_at = models.DateTimeField(_('آخر محاولة'), null=True, blank=True)
    completed_at = models.DateTimeField(_('تاريخ الإكمال'), null=True, blank=True)
    
    # تتبع التغييرات
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('سجل إرسال')
        verbose_name_plural = _('سجلات الإرسال')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'attempt_count']),
            models.Index(fields=['notification', 'status']),
        ]
    
    def __str__(self):
        return f"{self.notification.title} -> {self.recipient.get_full_name()} [{self.get_status_display()}]"
    
    @property
    def can_retry(self):
        """يمكن إعادة المحاولة؟"""
        return self.status in [self.Status.FAILED, self.Status.RETRYING] and self.attempt_count < self.max_attempts
    
    @property
    def is_successful(self):
        """هل تم الإرسال بنجاح؟"""
        return self.status == self.Status.SUCCESS


class WebhookEndpoint(models.Model):
    """نقاط النهاية للWebhook"""
    
    class EndpointType(models.TextChoices):
        PRIMARY = 'primary', _('رئيسي')
        SECONDARY = 'secondary', _('ثانوي')
        TEST = 'test', _('اختبار')
    
    name = models.CharField(_('الاسم'), max_length=100)
    url = models.URLField(_('الرابط'))
    endpoint_type = models.CharField(
        _('نوع النقطة'),
        max_length=20,
        choices=EndpointType.choices,
        default=EndpointType.PRIMARY
    )
    is_active = models.BooleanField(_('نشط'), default=True)
    timeout_seconds = models.PositiveIntegerField(_('مهلة الانتظار (ثانية)'), default=30)
    headers = models.JSONField(_('الهيدرز المخصصة'), default=dict, blank=True)
    
    # التتبع
    last_used_at = models.DateTimeField(_('آخر استخدام'), null=True, blank=True)
    success_count = models.PositiveIntegerField(_('عدد النجاحات'), default=0)
    failure_count = models.PositiveIntegerField(_('عدد الفشل'), default=0)
    
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('نقطة Webhook')
        verbose_name_plural = _('نقاط Webhook')
        ordering = ['endpoint_type', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_endpoint_type_display()})"


class NotificationAuditLog(models.Model):
    """سجل تدقيق التغييرات - من أنشأ/عدل/أرسل"""
    
    class ActionType(models.TextChoices):
        CREATED = 'created', _('إنشاء')
        UPDATED = 'updated', _('تعديل')
        DELETED = 'deleted', _('حذف')
        SENT = 'sent', _('إرسال')
        CANCELLED = 'cancelled', _('إلغاء')
        ENABLED = 'enabled', _('تفعيل')
        DISABLED = 'disabled', _('تعطيل')
    
    notification = models.ForeignKey(
        ScheduledNotification,
        on_delete=models.CASCADE,
        related_name='audit_logs',
        verbose_name=_('الإشعار')
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_('المستخدم')
    )
    action = models.CharField(
        _('الإجراء'),
        max_length=20,
        choices=ActionType.choices
    )
    changes = models.JSONField(_('التغييرات'), default=dict, blank=True)
    ip_address = models.GenericIPAddressField(_('عنوان IP'), null=True, blank=True)
    user_agent = models.TextField(_('وكيل المستخدم'), blank=True)
    created_at = models.DateTimeField(_('التاريخ'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('سجل تدقيق')
        verbose_name_plural = _('سجلات التدقيق')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.notification.title} - {self.get_action_display()} - {self.created_at}"
