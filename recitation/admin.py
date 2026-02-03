"""
إدارة نماذج التسميع
"""
from django.contrib import admin
from .models import RecitationRecord, RecitationError, MemorizationProgress, DailyGoal


class RecitationErrorInline(admin.TabularInline):
    model = RecitationError
    extra = 0


@admin.register(RecitationRecord)
class RecitationRecordAdmin(admin.ModelAdmin):
    """إدارة سجلات التسميع"""
    list_display = ['student', 'session', 'surah_start', 'recitation_type',
                   'grade', 'grade_level', 'total_errors', 'created_at']
    list_filter = ['recitation_type', 'grade_level', 'created_at']
    search_fields = ['student__first_name', 'student__last_name', 'notes']
    raw_id_fields = ['student', 'session', 'surah_start', 'surah_end']
    date_hierarchy = 'created_at'
    inlines = [RecitationErrorInline]


@admin.register(RecitationError)
class RecitationErrorAdmin(admin.ModelAdmin):
    """إدارة أخطاء التسميع"""
    list_display = ['record', 'surah', 'ayah', 'error_type', 'severity', 'created_at']
    list_filter = ['error_type', 'severity']
    search_fields = ['word_text', 'notes']
    raw_id_fields = ['record', 'surah']


@admin.register(MemorizationProgress)
class MemorizationProgressAdmin(admin.ModelAdmin):
    """إدارة تقدم الحفظ"""
    list_display = ['student', 'surah', 'ayah_from', 'ayah_to',
                   'is_memorized', 'is_reviewed', 'average_grade']
    list_filter = ['is_memorized', 'is_reviewed', 'surah']
    search_fields = ['student__first_name', 'student__last_name']
    raw_id_fields = ['student', 'surah']


@admin.register(DailyGoal)
class DailyGoalAdmin(admin.ModelAdmin):
    """إدارة الأهداف اليومية"""
    list_display = ['student', 'date', 'target_new_lines', 'actual_new_lines',
                   'target_review_pages', 'actual_review_pages', 'is_achieved']
    list_filter = ['is_achieved', 'date']
    search_fields = ['student__first_name', 'student__last_name']
    raw_id_fields = ['student']
    date_hierarchy = 'date'
