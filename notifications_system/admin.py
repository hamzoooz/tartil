"""
لوحة إدارة نظام النشر
Admin for Notification System
"""
from django.contrib import admin
from .models import (
    NotificationTemplate,
    ScheduledNotification,
    NotificationDispatchLog,
    NotificationAuditLog,
    WebhookEndpoint,
)


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'content_type', 'is_active', 'created_at']
    list_filter = ['content_type', 'is_active']
    search_fields = ['name', 'title_template']


@admin.register(ScheduledNotification)
class ScheduledNotificationAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'content_type', 'target_type', 'scheduled_datetime',
        'status', 'is_enabled', 'total_recipients', 'created_by'
    ]
    list_filter = ['status', 'content_type', 'target_type', 'is_enabled']
    search_fields = ['title', 'message']
    date_hierarchy = 'scheduled_datetime'
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'sent_at',
        'total_recipients', 'successful_sends', 'failed_sends'
    ]


@admin.register(NotificationDispatchLog)
class NotificationDispatchLogAdmin(admin.ModelAdmin):
    list_display = ['notification', 'recipient', 'status', 'attempt_count', 'created_at']
    list_filter = ['status', 'webhook_url']
    search_fields = ['notification__title', 'recipient__username']


@admin.register(NotificationAuditLog)
class NotificationAuditLogAdmin(admin.ModelAdmin):
    list_display = ['notification', 'user', 'action', 'created_at']
    list_filter = ['action']
    search_fields = ['notification__title', 'user__username']


@admin.register(WebhookEndpoint)
class WebhookEndpointAdmin(admin.ModelAdmin):
    list_display = ['name', 'url', 'endpoint_type', 'is_active', 'success_count', 'failure_count']
    list_filter = ['endpoint_type', 'is_active']
