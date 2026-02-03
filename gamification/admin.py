"""
إدارة نماذج التلعيب
"""
from django.contrib import admin
from .models import (Badge, StudentBadge, PointsLog, Streak,
                    Achievement, StudentAchievement, Leaderboard)


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    """إدارة الأوسمة"""
    list_display = ['name', 'badge_type', 'level', 'points_reward', 'is_active']
    list_filter = ['badge_type', 'level', 'is_active']
    search_fields = ['name', 'description']


@admin.register(StudentBadge)
class StudentBadgeAdmin(admin.ModelAdmin):
    """إدارة أوسمة الطلاب"""
    list_display = ['student', 'badge', 'earned_date']
    list_filter = ['badge', 'earned_date']
    search_fields = ['student__first_name', 'student__last_name', 'badge__name']
    raw_id_fields = ['student', 'badge']
    date_hierarchy = 'earned_date'


@admin.register(PointsLog)
class PointsLogAdmin(admin.ModelAdmin):
    """إدارة سجل النقاط"""
    list_display = ['student', 'points', 'points_type', 'reason', 'created_at']
    list_filter = ['points_type', 'created_at']
    search_fields = ['student__first_name', 'student__last_name', 'reason']
    raw_id_fields = ['student']
    date_hierarchy = 'created_at'


@admin.register(Streak)
class StreakAdmin(admin.ModelAdmin):
    """إدارة المواظبة"""
    list_display = ['student', 'current_streak', 'longest_streak',
                   'last_activity_date', 'total_active_days']
    search_fields = ['student__first_name', 'student__last_name']
    raw_id_fields = ['student']


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    """إدارة الإنجازات"""
    list_display = ['name', 'achievement_type', 'points_reward', 'target_value', 'is_active']
    list_filter = ['achievement_type', 'is_active']
    search_fields = ['name', 'description']


@admin.register(StudentAchievement)
class StudentAchievementAdmin(admin.ModelAdmin):
    """إدارة إنجازات الطلاب"""
    list_display = ['student', 'achievement', 'progress', 'is_completed', 'completed_date']
    list_filter = ['is_completed', 'achievement']
    search_fields = ['student__first_name', 'student__last_name']
    raw_id_fields = ['student', 'achievement']


@admin.register(Leaderboard)
class LeaderboardAdmin(admin.ModelAdmin):
    """إدارة لوحة المتصدرين"""
    list_display = ['student', 'period_type', 'period_start', 'period_end',
                   'total_points', 'rank']
    list_filter = ['period_type']
    search_fields = ['student__first_name', 'student__last_name']
    raw_id_fields = ['student']
