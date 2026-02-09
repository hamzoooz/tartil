"""
إدارة نماذج المستخدمين
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import CustomUser, StudentProfile, SheikhProfile, Notification, ActivityLog


class StudentProfileInline(admin.StackedInline):
    model = StudentProfile
    can_delete = False
    verbose_name = _('ملف الطالب')
    verbose_name_plural = _('ملف الطالب')
    fields = ['parent', 'current_surah', 'current_ayah', 'total_memorized_pages', 
              'total_memorized_juz', 'memorization_start_date', 'target_completion_date', 
              'notes', 'total_points']
    readonly_fields = ['total_memorized_pages', 'total_memorized_juz', 'total_points']


class SheikhProfileInline(admin.StackedInline):
    model = SheikhProfile
    can_delete = False
    verbose_name = _('ملف الشيخ')
    verbose_name_plural = _('ملف الشيخ')
    fields = ['specialization', 'ijazah_info', 'years_of_experience', 'max_students',
              'available_days', 'available_times', 'hourly_rate', 'rating', 'total_sessions']
    readonly_fields = ['rating', 'total_sessions']


class NotificationInline(admin.TabularInline):
    model = Notification
    extra = 0
    fields = ['notification_type', 'title', 'is_read', 'created_at']
    readonly_fields = ['created_at']
    can_delete = False
    max_num = 10
    verbose_name = _('إشعار')
    verbose_name_plural = _('الإشعارات الأخيرة')


class ActivityLogInline(admin.TabularInline):
    model = ActivityLog
    extra = 0
    fields = ['action', 'ip_address', 'created_at']
    readonly_fields = ['action', 'ip_address', 'created_at']
    can_delete = False
    max_num = 10
    verbose_name = _('نشاط')
    verbose_name_plural = _('سجل النشاطات')


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """إدارة المستخدمين"""
    list_display = ['username', 'email', 'first_name', 'last_name', 'user_type', 'is_active', 'date_joined']
    list_filter = ['user_type', 'is_active', 'gender', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'phone']
    ordering = ['-date_joined']
    
    def get_inlines(self, request, obj=None):
        """عرض inline حسب نوع المستخدم"""
        if obj is None:
            return []
        
        inlines = [NotificationInline, ActivityLogInline]
        
        if obj.user_type == 'student':
            inlines.insert(0, StudentProfileInline)
        elif obj.user_type == 'sheikh':
            inlines.insert(0, SheikhProfileInline)
        
        return inlines

    fieldsets = UserAdmin.fieldsets + (
        (_('معلومات إضافية'), {
            'fields': ('user_type', 'phone', 'gender', 'profile_image', 'bio',
                      'date_of_birth', 'country', 'city', 'is_active_member')
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        (_('معلومات إضافية'), {
            'fields': ('user_type', 'phone', 'gender', 'first_name', 'last_name')
        }),
    )


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    """إدارة ملفات الطلاب"""
    list_display = ['user', 'current_surah', 'total_memorized_pages', 'total_points', 'parent', 'memorization_start_date']
    list_filter = ['memorization_start_date']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']
    raw_id_fields = ['user', 'parent']
    readonly_fields = ['total_memorized_pages', 'total_memorized_juz', 'memorization_percentage']
    
    fieldsets = (
        (_('المستخدم'), {
            'fields': ('user', 'parent')
        }),
        (_('الموقع الحالي'), {
            'fields': ('current_surah', 'current_ayah')
        }),
        (_('إحصائيات الحفظ'), {
            'fields': ('total_memorized_pages', 'total_memorized_juz', 'memorization_percentage')
        }),
        (_('التواريخ'), {
            'fields': ('memorization_start_date', 'target_completion_date')
        }),
        (_('معلومات إضافية'), {
            'fields': ('total_points', 'notes')
        }),
    )


@admin.register(SheikhProfile)
class SheikhProfileAdmin(admin.ModelAdmin):
    """إدارة ملفات المشايخ"""
    list_display = ['user', 'specialization', 'years_of_experience', 'rating', 'total_sessions', 'max_students']
    list_filter = ['specialization']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']
    raw_id_fields = ['user']
    readonly_fields = ['rating', 'total_sessions']
    
    fieldsets = (
        (_('المستخدم'), {
            'fields': ('user',)
        }),
        (_('المعلومات المهنية'), {
            'fields': ('specialization', 'ijazah_info', 'years_of_experience')
        }),
        (_('إدارة الحلقات'), {
            'fields': ('max_students', 'available_days', 'available_times')
        }),
        (_('الإحصائيات'), {
            'fields': ('rating', 'total_sessions', 'hourly_rate')
        }),
    )


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """إدارة الإشعارات"""
    list_display = ['title', 'user', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['title', 'message', 'user__username']
    raw_id_fields = ['user']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at']
    
    actions = ['mark_as_read', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)
    mark_as_read.short_description = _('تحديد كمقروء')
    
    def mark_as_unread(self, request, queryset):
        queryset.update(is_read=False)
    mark_as_unread.short_description = _('تحديد كغير مقروء')


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    """إدارة سجل النشاط"""
    list_display = ['user', 'action', 'ip_address', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'action', 'details']
    raw_id_fields = ['user']
    date_hierarchy = 'created_at'
    readonly_fields = ['user', 'action', 'details', 'ip_address', 'created_at']
