"""
إدارة نماذج التلعيب
"""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import (Badge, StudentBadge, PointsLog, Streak,
                    Achievement, StudentAchievement, Leaderboard)


class StudentBadgeInline(admin.TabularInline):
    """أوسمة الطالب"""
    model = StudentBadge
    extra = 0
    fields = ['badge', 'earned_date', 'notes']
    raw_id_fields = ['badge']
    autocomplete_fields = ['badge']
    verbose_name = _('وسام')
    verbose_name_plural = _('الأوسمة المكتسبة')


class PointsLogInline(admin.TabularInline):
    """سجل نقاط الطالب"""
    model = PointsLog
    extra = 0
    fields = ['points', 'points_type', 'reason', 'created_at']
    readonly_fields = ['created_at']
    verbose_name = _('سجل نقاط')
    verbose_name_plural = _('سجل النقاط')


class StudentAchievementInline(admin.TabularInline):
    """إنجازات الطالب"""
    model = StudentAchievement
    extra = 0
    fields = ['achievement', 'progress', 'is_completed', 'completed_date']
    raw_id_fields = ['achievement']
    autocomplete_fields = ['achievement']
    verbose_name = _('إنجاز')
    verbose_name_plural = _('الإنجازات')


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    """إدارة الأوسمة"""
    list_display = ['name', 'badge_type', 'level', 'points_reward', 'criteria_type', 'is_active']
    list_filter = ['badge_type', 'level', 'is_active']
    search_fields = ['name', 'description']
    
    fieldsets = (
        ('معلومات أساسية', {
            'fields': ('name', 'name_english', 'description', 'icon', 'image')
        }),
        ('التصنيف', {
            'fields': ('badge_type', 'level', 'is_active')
        }),
        ('المكافآت والمعايير', {
            'fields': ('points_reward', 'criteria_type', 'criteria_value')
        }),
    )


@admin.register(StudentBadge)
class StudentBadgeAdmin(admin.ModelAdmin):
    """إدارة أوسمة الطلاب"""
    list_display = ['student', 'badge', 'earned_date']
    list_filter = ['badge__badge_type', 'badge__level', 'earned_date']
    search_fields = ['student__first_name', 'student__last_name', 'student__username', 'badge__name']
    raw_id_fields = ['student', 'badge']
    autocomplete_fields = ['student', 'badge']
    date_hierarchy = 'earned_date'


@admin.register(PointsLog)
class PointsLogAdmin(admin.ModelAdmin):
    """إدارة سجل النقاط"""
    list_display = ['student', 'points', 'points_type', 'reason', 'created_at']
    list_filter = ['points_type', 'created_at']
    search_fields = ['student__first_name', 'student__last_name', 'student__username', 'reason']
    raw_id_fields = ['student']
    autocomplete_fields = ['student']
    date_hierarchy = 'created_at'


@admin.register(Streak)
class StreakAdmin(admin.ModelAdmin):
    """إدارة المواظبة"""
    list_display = ['student', 'current_streak', 'longest_streak',
                   'last_activity_date', 'total_active_days']
    list_filter = ['current_streak', 'last_activity_date']
    search_fields = ['student__first_name', 'student__last_name', 'student__username']
    raw_id_fields = ['student']
    autocomplete_fields = ['student']


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    """إدارة الإنجازات"""
    list_display = ['name', 'achievement_type', 'points_reward', 'target_value', 'is_active']
    list_filter = ['achievement_type', 'is_active']
    search_fields = ['name', 'description']


@admin.register(StudentAchievement)
class StudentAchievementAdmin(admin.ModelAdmin):
    """إدارة إنجازات الطلاب"""
    list_display = ['student', 'achievement', 'progress', 'progress_percentage_display', 'is_completed', 'completed_date']
    list_filter = ['is_completed', 'achievement__achievement_type']
    search_fields = ['student__first_name', 'student__last_name', 'student__username', 'achievement__name']
    raw_id_fields = ['student', 'achievement']
    autocomplete_fields = ['student', 'achievement']
    
    def progress_percentage_display(self, obj):
        return f"{obj.progress_percentage}%"
    progress_percentage_display.short_description = 'نسبة التقدم'


@admin.register(Leaderboard)
class LeaderboardAdmin(admin.ModelAdmin):
    """إدارة لوحة المتصدرين"""
    list_display = ['student', 'period_type', 'period_start', 'period_end',
                   'total_points', 'rank']
    list_filter = ['period_type', 'period_start']
    search_fields = ['student__first_name', 'student__last_name', 'student__username']
    raw_id_fields = ['student']
    autocomplete_fields = ['student']
    ordering = ['-period_start', 'rank']
