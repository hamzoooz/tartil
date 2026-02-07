"""
إعدادات لوحة التحكم المتقدمة - Advanced Admin Dashboard Configurations
"""
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.db.models import Count, Sum, Avg, Q
from django.urls import path, reverse
from django.http import JsonResponse
from django.shortcuts import render

from .models import (
    DashboardSettings, DashboardWidget, DashboardLayout,
    DashboardLayoutWidget, AdminActionLog, BulkAction
)

User = get_user_model()


# ==================== Inline Classes ====================

class DashboardLayoutWidgetInline(admin.TabularInline):
    model = DashboardLayoutWidget
    extra = 1
    autocomplete_fields = ['widget']


# ==================== Dashboard Settings Admin ====================

@admin.register(DashboardSettings)
class DashboardSettingsAdmin(admin.ModelAdmin):
    list_display = ['user', 'theme', 'items_per_page', 'sidebar_collapsed', 'updated_at']
    list_filter = ['theme', 'items_per_page', 'email_notifications', 'push_notifications']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (_('المستخدم'), {
            'fields': ('user',)
        }),
        (_('إعدادات العرض'), {
            'fields': ('theme', 'sidebar_collapsed', 'items_per_page')
        }),
        (_('إعدادات الإشعارات'), {
            'fields': ('email_notifications', 'push_notifications')
        }),
        (_('إعدادات متقدمة'), {
            'fields': ('hidden_columns', 'table_ordering'),
            'classes': ('collapse',)
        }),
        (_('التواريخ'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# ==================== Dashboard Widget Admin ====================

@admin.register(DashboardWidget)
class DashboardWidgetAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'widget_type_display', 'data_source', 'color_badge',
        'width', 'order', 'is_active', 'is_default'
    ]
    list_filter = ['widget_type', 'data_source', 'color', 'is_active', 'is_default']
    search_fields = ['name', 'title', 'subtitle']
    list_editable = ['width', 'order', 'is_active']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (_('معلومات أساسية'), {
            'fields': ('name', 'widget_type', 'data_source')
        }),
        (_('إعدادات العرض'), {
            'fields': ('title', 'subtitle', 'icon', 'color')
        }),
        (_('الحجم والموقع'), {
            'fields': ('width', 'height', 'order')
        }),
        (_('إعدادات البيانات'), {
            'fields': ('filter_conditions', 'date_range'),
            'classes': ('collapse',)
        }),
        (_('الحالة'), {
            'fields': ('is_active', 'is_default')
        }),
        (_('التواريخ'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def widget_type_display(self, obj):
        icons = {
            'stats_card': '📊',
            'chart_line': '📈',
            'chart_bar': '📊',
            'chart_pie': '🥧',
            'chart_doughnut': '🍩',
            'table': '📋',
            'list': '📃',
            'calendar': '📅',
            'progress': '⏳',
            'recent_activity': '🔔',
        }
        return format_html(
            '{} {}',
            icons.get(obj.widget_type, '📦'),
            obj.get_widget_type_display()
        )
    widget_type_display.short_description = _('نوع الأداة')
    
    def color_badge(self, obj):
        colors = {
            'primary': '#0d6efd',
            'secondary': '#6c757d',
            'success': '#198754',
            'danger': '#dc3545',
            'warning': '#ffc107',
            'info': '#0dcaf0',
            'dark': '#212529',
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 10px; font-size: 12px;">{}</span>',
            colors.get(obj.color, '#6c757d'),
            obj.get_color_display()
        )
    color_badge.short_description = _('اللون')


# ==================== Dashboard Layout Admin ====================

@admin.register(DashboardLayout)
class DashboardLayoutAdmin(admin.ModelAdmin):
    list_display = ['name', 'user_display', 'widgets_count', 'is_default', 'is_system', 'updated_at']
    list_filter = ['is_default', 'is_system']
    search_fields = ['name', 'description']
    inlines = [DashboardLayoutWidgetInline]
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (_('معلومات أساسية'), {
            'fields': ('name', 'description')
        }),
        (_('المالك'), {
            'fields': ('user',)
        }),
        (_('الإعدادات'), {
            'fields': ('is_default', 'is_system')
        }),
        (_('التواريخ'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def user_display(self, obj):
        if obj.user:
            return obj.user.get_full_name() or obj.user.username
        return format_html('<span style="color: #198754;">{}</span>', _('نظامي'))
    user_display.short_description = _('المستخدم')
    
    def widgets_count(self, obj):
        return obj.widgets.count()
    widgets_count.short_description = _('عدد الأدوات')


# ==================== Admin Action Log Admin ====================

@admin.register(AdminActionLog)
class AdminActionLogAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user_display', 'action_badge', 'model_name', 
        'object_repr_short', 'ip_address', 'created_at'
    ]
    list_filter = ['action_type', 'model_name', 'created_at']
    search_fields = ['user__username', 'user__first_name', 'object_repr', 'ip_address']
    readonly_fields = [
        'user', 'action_type', 'model_name', 'object_id', 'object_repr',
        'changes_formatted', 'ip_address', 'user_agent', 'created_at'
    ]
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (_('المستخدم'), {
            'fields': ('user', 'ip_address', 'user_agent')
        }),
        (_('الإجراء'), {
            'fields': ('action_type', 'model_name', 'object_id', 'object_repr')
        }),
        (_('التغييرات'), {
            'fields': ('changes_formatted',)
        }),
        (_('التاريخ'), {
            'fields': ('created_at',)
        }),
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def user_display(self, obj):
        if obj.user:
            return obj.user.get_full_name() or obj.user.username
        return format_html('<span style="color: #dc3545;">{}</span>', _('غير معروف'))
    user_display.short_description = _('المستخدم')
    
    def action_badge(self, obj):
        colors = {
            'create': '#198754',
            'update': '#0d6efd',
            'delete': '#dc3545',
            'view': '#6c757d',
            'export': '#0dcaf0',
            'import': '#ffc107',
            'login': '#20c997',
            'logout': '#fd7e14',
            'other': '#6c757d',
        }
        icons = {
            'create': '➕',
            'update': '✏️',
            'delete': '🗑️',
            'view': '👁️',
            'export': '📤',
            'import': '📥',
            'login': '🔑',
            'logout': '🚪',
            'other': '📌',
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 10px; font-size: 12px;">{} {}</span>',
            colors.get(obj.action_type, '#6c757d'),
            icons.get(obj.action_type, '📌'),
            obj.get_action_type_display()
        )
    action_badge.short_description = _('الإجراء')
    
    def object_repr_short(self, obj):
        if len(obj.object_repr) > 50:
            return obj.object_repr[:50] + '...'
        return obj.object_repr
    object_repr_short.short_description = _('الكائن')
    
    def changes_formatted(self, obj):
        if not obj.changes:
            return '-'
        html = '<table style="width: 100%; border-collapse: collapse;">'
        html += '<tr style="background-color: #f8f9fa;">'
        html += '<th style="border: 1px solid #dee2e6; padding: 8px;">الحقل</th>'
        html += '<th style="border: 1px solid #dee2e6; padding: 8px;">القيمة القديمة</th>'
        html += '<th style="border: 1px solid #dee2e6; padding: 8px;">القيمة الجديدة</th>'
        html += '</tr>'
        for field, values in obj.changes.items():
            old_val = values.get('old', '-')
            new_val = values.get('new', '-')
            html += f'<tr><td style="border: 1px solid #dee2e6; padding: 8px;"><strong>{field}</strong></td>'
            html += f'<td style="border: 1px solid #dee2e6; padding: 8px; color: #dc3545;">{old_val}</td>'
            html += f'<td style="border: 1px solid #dee2e6; padding: 8px; color: #198754;">{new_val}</td></tr>'
        html += '</table>'
        return format_html(html)
    changes_formatted.short_description = _('التغييرات')


# ==================== Bulk Action Admin ====================

@admin.register(BulkAction)
class BulkActionAdmin(admin.ModelAdmin):
    list_display = ['name', 'model_name', 'action_type_display', 'created_by', 'is_active', 'created_at']
    list_filter = ['action_type', 'model_name', 'is_active']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (_('معلومات أساسية'), {
            'fields': ('name', 'description', 'created_by')
        }),
        (_('إعدادات الإجراء'), {
            'fields': ('model_name', 'action_type')
        }),
        (_('الإعدادات المتقدمة'), {
            'fields': ('field_updates', 'filter_conditions'),
            'classes': ('collapse',)
        }),
        (_('الحالة'), {
            'fields': ('is_active',)
        }),
        (_('التواريخ'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def action_type_display(self, obj):
        icons = {
            'delete': '🗑️',
            'update': '✏️',
            'export': '📤',
            'notify': '🔔',
            'change_status': '🔄',
        }
        return format_html(
            '{} {}',
            icons.get(obj.action_type, '📌'),
            obj.get_action_type_display()
        )
    action_type_display.short_description = _('نوع الإجراء')
