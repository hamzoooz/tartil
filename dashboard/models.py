"""
نماذج لوحة التحكم المتقدمة
Dashboard Models for Advanced Admin Control
"""
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import json


class DashboardSettings(models.Model):
    """إعدادات لوحة التحكم للمستخدم"""
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='dashboard_settings',
        verbose_name=_('المستخدم')
    )
    
    # إعدادات العرض
    theme = models.CharField(_('السمة'), max_length=20, default='light', choices=[
        ('light', _('فاتح')),
        ('dark', _('داكن')),
        ('auto', _('تلقائي')),
    ])
    
    sidebar_collapsed = models.BooleanField(_('القائمة الجانبية مطوية'), default=False)
    
    # إعدادات الجداول
    items_per_page = models.PositiveIntegerField(_('عناصر لكل صفحة'), default=25, choices=[
        (10, '10'),
        (25, '25'),
        (50, '50'),
        (100, '100'),
        (200, '200'),
    ])
    
    # إعدادات الإشعارات
    email_notifications = models.BooleanField(_('إشعارات البريد'), default=True)
    push_notifications = models.BooleanField(_('إشعارات المتصفح'), default=True)
    
    # إعدادات متقدمة - تخصيص الأعمدة المعروضة لكل نموذج
    hidden_columns = models.JSONField(_('الأعمدة المخفية'), default=dict, blank=True)
    
    # ترتيب الجداول المفضل
    table_ordering = models.JSONField(_('ترتيب الجداول'), default=dict, blank=True)
    
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    updated_at = models.DateTimeField(_('تاريخ التحديث'), auto_now=True)
    
    class Meta:
        verbose_name = _('إعدادات لوحة التحكم')
        verbose_name_plural = _('إعدادات لوحة التحكم')
    
    def __str__(self):
        return f"إعدادات {self.user.get_full_name()}"
    
    def get_hidden_columns(self, model_name):
        """الحصول على الأعمدة المخفية لنموذج معين"""
        return self.hidden_columns.get(model_name, [])
    
    def set_hidden_columns(self, model_name, columns):
        """تعيين الأعمدة المخفية لنموذج معين"""
        self.hidden_columns[model_name] = columns
        self.save(update_fields=['hidden_columns'])


class DashboardWidget(models.Model):
    """الأدوات/الWidgets القابلة للتخصيص في لوحة التحكم"""
    
    class WidgetType(models.TextChoices):
        STATS_CARD = 'stats_card', _('بطاقة إحصائيات')
        CHART_LINE = 'chart_line', _('رسم خطي')
        CHART_BAR = 'chart_bar', _('رسم أعمدة')
        CHART_PIE = 'chart_pie', _('رسم دائري')
        CHART_DOUGHNUT = 'chart_doughnut', _('رسم دائري مجوف')
        TABLE = 'table', _('جدول')
        LIST = 'list', _('قائمة')
        CALENDAR = 'calendar', _('تقويم')
        PROGRESS = 'progress', _('شريط تقدم')
        RECENT_ACTIVITY = 'recent_activity', _('النشاط الأخير')
        
    class DataSource(models.TextChoices):
        USERS = 'users', _('المستخدمين')
        STUDENTS = 'students', _('الطلاب')
        SHEIKHS = 'sheikhs', _('المشايخ')
        HALAQAT = 'halaqat', _('الحلقات')
        SESSIONS = 'sessions', _('الجلسات')
        RECITATIONS = 'recitations', _('التسميعات')
        ATTENDANCE = 'attendance', _('الحضور')
        POINTS = 'points', _('النقاط')
        BADGES = 'badges', _('الأوسمة')
        CERTIFICATES = 'certificates', _('الشهادات')
        CUSTOM = 'custom', _('مخصص')
    
    name = models.CharField(_('اسم الأداة'), max_length=100)
    widget_type = models.CharField(_('نوع الأداة'), max_length=20, choices=WidgetType.choices)
    data_source = models.CharField(_('مصدر البيانات'), max_length=20, choices=DataSource.choices)
    
    # إعدادات العرض
    title = models.CharField(_('العنوان'), max_length=200)
    subtitle = models.CharField(_('العنوان الفرعي'), max_length=200, blank=True)
    icon = models.CharField(_('الأيقونة'), max_length=50, default='fa-chart-line')
    color = models.CharField(_('اللون'), max_length=20, default='primary', choices=[
        ('primary', _('أزرق')),
        ('secondary', _('رمادي')),
        ('success', _('أخضر')),
        ('danger', _('أحمر')),
        ('warning', _('أصفر')),
        ('info', _('سماوي')),
        ('dark', _('داكن')),
    ])
    
    # إعدادات الحجم والموقع
    width = models.PositiveIntegerField(_('العرض (أعمدة)'), default=4, help_text=_('من 1 إلى 12'))
    height = models.PositiveIntegerField(_('الارتفاع (بكسل)'), default=300, blank=True, null=True)
    order = models.PositiveIntegerField(_('الترتيب'), default=0)
    
    # إعدادات البيانات
    filter_conditions = models.JSONField(_('شروط التصفية'), default=dict, blank=True)
    date_range = models.CharField(_('نطاق التاريخ'), max_length=20, default='all', choices=[
        ('today', _('اليوم')),
        ('week', _('هذا الأسبوع')),
        ('month', _('هذا الشهر')),
        ('quarter', _('هذا الربع')),
        ('year', _('هذا العام')),
        ('all', _('الكل')),
    ])
    
    # حالة الأداة
    is_active = models.BooleanField(_('نشط'), default=True)
    is_default = models.BooleanField(_('افتراضي'), default=False)
    
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    updated_at = models.DateTimeField(_('تاريخ التحديث'), auto_now=True)
    
    class Meta:
        verbose_name = _('أداة لوحة التحكم')
        verbose_name_plural = _('أدوات لوحة التحكم')
        ordering = ['order', 'created_at']
    
    def __str__(self):
        return self.title


class DashboardLayout(models.Model):
    """تخطيطات لوحة التحكم المخصصة"""
    
    name = models.CharField(_('اسم التخطيط'), max_length=100)
    description = models.TextField(_('الوصف'), blank=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='dashboard_layouts',
        verbose_name=_('المستخدم'),
        null=True, blank=True
    )
    
    # الأدوات المضمنة
    widgets = models.ManyToManyField(
        DashboardWidget,
        through='DashboardLayoutWidget',
        related_name='layouts',
        verbose_name=_('الأدوات')
    )
    
    # إعدادات
    is_default = models.BooleanField(_('افتراضي'), default=False)
    is_system = models.BooleanField(_('نظامي'), default=False)
    
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    updated_at = models.DateTimeField(_('تاريخ التحديث'), auto_now=True)
    
    class Meta:
        verbose_name = _('تخطيط لوحة التحكم')
        verbose_name_plural = _('تخطيطات لوحة التحكم')
    
    def __str__(self):
        return self.name


class DashboardLayoutWidget(models.Model):
    """ربط التخطيط بالأدوات مع إعدادات خاصة"""
    
    layout = models.ForeignKey(DashboardLayout, on_delete=models.CASCADE)
    widget = models.ForeignKey(DashboardWidget, on_delete=models.CASCADE)
    
    # إعدادات مخصصة للتخطيط
    custom_width = models.PositiveIntegerField(_('عرض مخصص'), null=True, blank=True)
    custom_order = models.PositiveIntegerField(_('ترتيب مخصص'), default=0)
    custom_settings = models.JSONField(_('إعدادات مخصصة'), default=dict, blank=True)
    
    class Meta:
        verbose_name = _('أداة في التخطيط')
        verbose_name_plural = _('أدوات في التخطيط')
        ordering = ['custom_order']
        unique_together = ['layout', 'widget']


class AdminActionLog(models.Model):
    """سجل إجراءات المشرفين"""
    
    class ActionType(models.TextChoices):
        CREATE = 'create', _('إنشاء')
        UPDATE = 'update', _('تحديث')
        DELETE = 'delete', _('حذف')
        VIEW = 'view', _('عرض')
        EXPORT = 'export', _('تصدير')
        IMPORT = 'import', _('استيراد')
        LOGIN = 'login', _('تسجيل دخول')
        LOGOUT = 'logout', _('تسجيل خروج')
        OTHER = 'other', _('آخر')
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='admin_actions',
        verbose_name=_('المستخدم')
    )
    action_type = models.CharField(_('نوع الإجراء'), max_length=20, choices=ActionType.choices)
    model_name = models.CharField(_('اسم النموذج'), max_length=100)
    object_id = models.CharField(_('معرف الكائن'), max_length=100, blank=True)
    object_repr = models.CharField(_('تمثيل الكائن'), max_length=200, blank=True)
    
    # التفاصيل
    changes = models.JSONField(_('التغييرات'), default=dict, blank=True)
    ip_address = models.GenericIPAddressField(_('عنوان IP'), null=True, blank=True)
    user_agent = models.TextField(_('وكيل المستخدم'), blank=True)
    
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('سجل إجراء إداري')
        verbose_name_plural = _('سجل الإجراءات الإدارية')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user} - {self.get_action_type_display()} - {self.model_name}"


class BulkAction(models.Model):
    """الإجراءات الجماعية المحفوظة"""
    
    name = models.CharField(_('اسم الإجراء'), max_length=100)
    description = models.TextField(_('الوصف'), blank=True)
    
    model_name = models.CharField(_('اسم النموذج'), max_length=100)
    action_type = models.CharField(_('نوع الإجراء'), max_length=50, choices=[
        ('delete', _('حذف')),
        ('update', _('تحديث حقول')),
        ('export', _('تصدير')),
        ('notify', _('إرسال إشعار')),
        ('change_status', _('تغيير الحالة')),
    ])
    
    # إعدادات الإجراء
    field_updates = models.JSONField(_('الحقول للتحديث'), default=dict, blank=True)
    filter_conditions = models.JSONField(_('شروط التصفية'), default=dict, blank=True)
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_bulk_actions',
        verbose_name=_('تم الإنشاء بواسطة')
    )
    
    is_active = models.BooleanField(_('نشط'), default=True)
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    updated_at = models.DateTimeField(_('تاريخ التحديث'), auto_now=True)
    
    class Meta:
        verbose_name = _('إجراء جماعي')
        verbose_name_plural = _('الإجراءات الجماعية')
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name


# ==================== نظام الرسائل والإشعارات ====================

class Message(models.Model):
    """نموذج الرسائل بين المستخدمين"""
    
    class MessageType(models.TextChoices):
        DIRECT = 'direct', _('رسالة مباشرة')
        BROADCAST = 'broadcast', _('رسالة جماعية')
        SYSTEM = 'system', _('رسالة نظام')
        ALERT = 'alert', _('تنبيه')
    
    class Priority(models.TextChoices):
        LOW = 'low', _('منخفض')
        NORMAL = 'normal', _('عادي')
        HIGH = 'high', _('عالي')
        URGENT = 'urgent', _('عاجل')
    
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages',
        verbose_name=_('المرسل')
    )
    recipients = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='received_messages',
        verbose_name=_('المستلمون'),
        blank=True
    )
    
    message_type = models.CharField(
        _('نوع الرسالة'),
        max_length=20,
        choices=MessageType.choices,
        default=MessageType.DIRECT
    )
    priority = models.CharField(
        _('الأولوية'),
        max_length=20,
        choices=Priority.choices,
        default=Priority.NORMAL
    )
    
    subject = models.CharField(_('الموضوع'), max_length=200)
    content = models.TextField(_('المحتوى'))
    
    # حالة القراءة
    read_by = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='read_messages',
        verbose_name=_('تم القراءة بواسطة'),
        blank=True
    )
    
    # مرفقات
    attachments = models.JSONField(_('المرفقات'), default=list, blank=True)
    
    # التحكم
    is_draft = models.BooleanField(_('مسودة'), default=False)
    is_archived = models.BooleanField(_('مؤرشفة'), default=False)
    expires_at = models.DateTimeField(_('تاريخ الانتهاء'), null=True, blank=True)
    
    created_at = models.DateTimeField(_('تاريخ الإرسال'), auto_now_add=True)
    updated_at = models.DateTimeField(_('تاريخ التحديث'), auto_now=True)
    
    class Meta:
        verbose_name = _('رسالة')
        verbose_name_plural = _('الرسائل')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.subject} - {self.sender}"
    
    def is_read_by(self, user):
        """هل قرأها المستخدم؟"""
        return self.read_by.filter(id=user.id).exists()
    
    def mark_as_read(self, user):
        """تحديد كمقروءة"""
        if not self.is_read_by(user):
            self.read_by.add(user)
    
    @property
    def unread_count(self):
        """عدد غير المقروءة"""
        if self.message_type == self.MessageType.BROADCAST:
            return self.recipients.count() - self.read_by.count()
        return 0


class Notification(models.Model):
    """نموذج الإشعارات"""
    
    class NotificationType(models.TextChoices):
        SESSION = 'session', _('جلسة')
        RECITATION = 'recitation', _('تسميع')
        ENROLLMENT = 'enrollment', _('تسجيل')
        CERTIFICATE = 'certificate', _('شهادة')
        BADGE = 'badge', _('وسام')
        POINTS = 'points', _('نقاط')
        SYSTEM = 'system', _('نظام')
        REMINDER = 'reminder', _('تذكير')
        ALERT = 'alert', _('تنبيه')
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='dashboard_notifications',
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
    
    # رابط للتنقل
    link = models.CharField(_('الرابط'), max_length=500, blank=True)
    link_text = models.CharField(_('نص الرابط'), max_length=100, default=_('عرض'))
    
    # البيانات الإضافية
    data = models.JSONField(_('بيانات إضافية'), default=dict, blank=True)
    
    # الحالة
    is_read = models.BooleanField(_('مقروء'), default=False)
    is_important = models.BooleanField(_('مهم'), default=False)
    
    # التنبيه
    shown_in_ui = models.BooleanField(_('ظهر في الواجهة'), default=False)
    email_sent = models.BooleanField(_('أُرسل بريد'), default=False)
    push_sent = models.BooleanField(_('أُرسل Push'), default=False)
    
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    read_at = models.DateTimeField(_('تاريخ القراءة'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('إشعار')
        verbose_name_plural = _('الإشعارات')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"
    
    def mark_as_read(self):
        """تحديد كمقروء"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])


class Alert(models.Model):
    """التنبيهات المهمة للإدارة"""
    
    class AlertType(models.TextChoices):
        INFO = 'info', _('معلومات')
        WARNING = 'warning', _('تحذير')
        ERROR = 'error', _('خطأ')
        SUCCESS = 'success', _('نجاح')
    
    alert_type = models.CharField(
        _('نوع التنبيه'),
        max_length=20,
        choices=AlertType.choices,
        default=AlertType.INFO
    )
    
    title = models.CharField(_('العنوان'), max_length=200)
    message = models.TextField(_('الرسالة'))
    
    # المستهدفون
    target_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='alerts',
        verbose_name=_('المستخدمون المستهدفون'),
        blank=True
    )
    target_roles = models.JSONField(
        _('الأدوار المستهدفة'),
        default=list,
        blank=True,
        help_text=_('مثل: ["admin", "sheikh"]')
    )
    
    # التحكم
    is_active = models.BooleanField(_('نشط'), default=True)
    show_once = models.BooleanField(_('إظهار مرة واحدة'), default=False)
    dismissible = models.BooleanField(_('قابل للإغلاق'), default=True)
    
    # المدة
    start_date = models.DateTimeField(_('تاريخ البدء'), default=timezone.now)
    end_date = models.DateTimeField(_('تاريخ الانتهاء'), null=True, blank=True)
    
    # الإحصائيات
    views_count = models.PositiveIntegerField(_('عدد المشاهدات'), default=0)
    dismissed_by = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='dismissed_alerts',
        verbose_name=_('تم إغلاقه بواسطة'),
        blank=True
    )
    
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_alerts',
        verbose_name=_('تم الإنشاء بواسطة')
    )
    
    class Meta:
        verbose_name = _('تنبيه')
        verbose_name_plural = _('التنبيهات')
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def is_visible_to(self, user):
        """هل التنبيه مرئي للمستخدم؟"""
        if not self.is_active:
            return False
        if self.end_date and timezone.now() > self.end_date:
            return False
        if self.show_once and self.dismissed_by.filter(id=user.id).exists():
            return False
        if self.target_users.exists() and not self.target_users.filter(id=user.id).exists():
            return False
        if self.target_roles and user.user_type not in self.target_roles:
            return False
        return True
    
    def dismiss(self, user):
        """إغلاق التنبيه"""
        self.dismissed_by.add(user)


# ==================== استيراد Excel ====================

class ExcelImportJob(models.Model):
    """سجل عمليات استيراد Excel"""
    
    class ImportType(models.TextChoices):
        STUDENTS = 'students', _('طلاب')
        SHEIKHS = 'sheikhs', _('مشايخ')
        HALAQAT = 'halaqat', _('حلقات')
    
    class Status(models.TextChoices):
        PENDING = 'pending', _('قيد الانتظار')
        PROCESSING = 'processing', _('جاري المعالجة')
        COMPLETED = 'completed', _('مكتمل')
        PARTIAL = 'partial', _('مكتمل جزئياً')
        FAILED = 'failed', _('فشل')
    
    import_type = models.CharField(
        _('نوع الاستيراد'),
        max_length=20,
        choices=ImportType.choices
    )
    
    file_name = models.CharField(_('اسم الملف'), max_length=255)
    file_path = models.FileField(_('الملف'), upload_to='imports/')
    
    status = models.CharField(
        _('الحالة'),
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    
    # الإعدادات
    create_accounts = models.BooleanField(_('إنشاء حسابات'), default=True)
    auto_distribute = models.BooleanField(_('توزيع تلقائي'), default=False)
    distribution_count = models.PositiveIntegerField(
        _('عدد الحلقات للتوزيع'),
        default=10,
        help_text=_('عدد الحلقات التي سيتم توزيع الطلاب عليها')
    )
    
    # النتائج
    total_rows = models.PositiveIntegerField(_('إجمالي الصفوف'), default=0)
    success_count = models.PositiveIntegerField(_('النجاح'), default=0)
    failed_count = models.PositiveIntegerField(_('الفشل'), default=0)
    skipped_count = models.PositiveIntegerField(_('التخطي'), default=0)
    
    errors_log = models.JSONField(_('سجل الأخطاء'), default=list, blank=True)
    created_users = models.JSONField(_('المستخدمون المنشأون'), default=list, blank=True)
    created_halaqat = models.JSONField(_('الحلقات المنشأة'), default=list, blank=True)
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='import_jobs',
        verbose_name=_('تم الإنشاء بواسطة')
    )
    
    started_at = models.DateTimeField(_('تاريخ البدء'), null=True, blank=True)
    completed_at = models.DateTimeField(_('تاريخ الإكمال'), null=True, blank=True)
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('عملية استيراد Excel')
        verbose_name_plural = _('عمليات استيراد Excel')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_import_type_display()} - {self.file_name}"
    
    @property
    def duration(self):
        """مدة المعالجة"""
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            return delta.total_seconds()
        return None
