"""
نماذج لوحة التحكم المتقدمة
Dashboard Models for Advanced Admin Control
"""
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
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
