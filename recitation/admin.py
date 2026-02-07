"""
إدارة نماذج التسميع
"""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import RecitationRecord, RecitationError, MemorizationProgress, DailyGoal


class RecitationErrorInline(admin.TabularInline):
    """أخطاء التسميع"""
    model = RecitationError
    extra = 0
    fields = ['surah', 'ayah', 'error_type', 'severity', 'word_text']
    raw_id_fields = ['surah']
    autocomplete_fields = ['surah']
    verbose_name = _('خطأ')
    verbose_name_plural = _('الأخطاء')


class MemorizationProgressInline(admin.TabularInline):
    """تقدم الحفظ للطالب"""
    model = MemorizationProgress
    extra = 0
    fields = ['surah', 'ayah_from', 'ayah_to', 'is_memorized', 'is_reviewed', 'average_grade']
    raw_id_fields = ['surah']
    autocomplete_fields = ['surah']
    verbose_name = _('تقدم سورة')
    verbose_name_plural = _('تقدم الحفظ')


class DailyGoalInline(admin.TabularInline):
    """الأهداف اليومية للطالب"""
    model = DailyGoal
    extra = 0
    fields = ['date', 'target_new_lines', 'actual_new_lines', 'target_review_pages', 'actual_review_pages', 'is_achieved']
    verbose_name = _('هدف يومي')
    verbose_name_plural = _('الأهداف اليومية')


@admin.register(RecitationRecord)
class RecitationRecordAdmin(admin.ModelAdmin):
    """إدارة سجلات التسميع"""
    list_display = ['student', 'session_display', 'surah_start', 'ayah_start', 'ayah_end', 
                   'recitation_type', 'grade', 'grade_level', 'total_errors', 'created_at']
    list_filter = ['recitation_type', 'grade_level', 'created_at', 'surah_start']
    search_fields = ['student__first_name', 'student__last_name', 'student__username', 'notes']
    raw_id_fields = ['student', 'session', 'surah_start', 'surah_end']
    autocomplete_fields = ['student', 'session', 'surah_start', 'surah_end']
    date_hierarchy = 'created_at'
    inlines = [RecitationErrorInline]
    
    fieldsets = (
        ('المعلومات الأساسية', {
            'fields': ('student', 'session', 'recitation_type')
        }),
        ('المحتوى المسمع', {
            'fields': ('surah_start', 'ayah_start', 'surah_end', 'ayah_end')
        }),
        ('التقييم', {
            'fields': ('grade', 'grade_level', 'total_errors', 'duration_minutes')
        }),
        ('الملاحظات', {
            'fields': ('notes', 'sheikh_feedback')
        }),
    )
    readonly_fields = ['grade_level']
    
    def session_display(self, obj):
        return f"{obj.session.halaqa.name} - {obj.session.date}"
    session_display.short_description = 'الجلسة'


@admin.register(RecitationError)
class RecitationErrorAdmin(admin.ModelAdmin):
    """إدارة أخطاء التسميع"""
    list_display = ['record_display', 'surah', 'ayah', 'error_type', 'severity', 'created_at']
    list_filter = ['error_type', 'severity', 'created_at']
    search_fields = ['word_text', 'notes']
    raw_id_fields = ['record', 'surah']
    autocomplete_fields = ['surah']
    
    def record_display(self, obj):
        return f"{obj.record.student.get_full_name()} - {obj.record.surah_start.name_arabic}"
    record_display.short_description = 'سجل التسميع'


@admin.register(MemorizationProgress)
class MemorizationProgressAdmin(admin.ModelAdmin):
    """إدارة تقدم الحفظ"""
    list_display = ['student', 'surah', 'ayah_from', 'ayah_to',
                   'is_memorized', 'is_reviewed', 'average_grade', 'last_review_date']
    list_filter = ['is_memorized', 'is_reviewed', 'surah', 'last_review_date']
    search_fields = ['student__first_name', 'student__last_name', 'student__username']
    raw_id_fields = ['student', 'surah']
    autocomplete_fields = ['student', 'surah']


@admin.register(DailyGoal)
class DailyGoalAdmin(admin.ModelAdmin):
    """إدارة الأهداف اليومية"""
    list_display = ['student', 'date', 'target_new_lines', 'actual_new_lines',
                   'target_review_pages', 'actual_review_pages', 'is_achieved']
    list_filter = ['is_achieved', 'date']
    search_fields = ['student__first_name', 'student__last_name', 'student__username']
    raw_id_fields = ['student']
    autocomplete_fields = ['student']
    date_hierarchy = 'date'
