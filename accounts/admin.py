"""
إدارة نماذج المستخدمين
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import CustomUser, StudentProfile, SheikhProfile, Notification, ActivityLog


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """إدارة المستخدمين"""
    list_display = ['username', 'email', 'first_name', 'last_name', 'user_type', 'is_active']
    list_filter = ['user_type', 'is_active', 'gender', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'phone']
    ordering = ['-date_joined']

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


class StudentProfileInline(admin.StackedInline):
    model = StudentProfile
    can_delete = False
    verbose_name = _('ملف الطالب')
    verbose_name_plural = _('ملف الطالب')


class SheikhProfileInline(admin.StackedInline):
    model = SheikhProfile
    can_delete = False
    verbose_name = _('ملف الشيخ')
    verbose_name_plural = _('ملف الشيخ')


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    """إدارة ملفات الطلاب"""
    list_display = ['user', 'current_surah', 'total_memorized_pages', 'total_points', 'parent']
    list_filter = ['memorization_start_date']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']
    raw_id_fields = ['user', 'parent']


@admin.register(SheikhProfile)
class SheikhProfileAdmin(admin.ModelAdmin):
    """إدارة ملفات المشايخ"""
    list_display = ['user', 'specialization', 'years_of_experience', 'rating', 'total_sessions']
    list_filter = ['specialization']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']
    raw_id_fields = ['user']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """إدارة الإشعارات"""
    list_display = ['title', 'user', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['title', 'message', 'user__username']
    raw_id_fields = ['user']
    date_hierarchy = 'created_at'


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    """إدارة سجل النشاط"""
    list_display = ['user', 'action', 'ip_address', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'action', 'details']
    raw_id_fields = ['user']
    date_hierarchy = 'created_at'
    readonly_fields = ['user', 'action', 'details', 'ip_address', 'created_at']
