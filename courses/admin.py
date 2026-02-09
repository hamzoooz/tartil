"""
Admin configuration for Courses app
"""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import (
    Curriculum, CurriculumLesson, StudentCurriculum,
    MotivationalQuote, QuoteNotification, TafseerLesson,
    ScheduledNotification, LessonReminder
)


class CurriculumLessonInline(admin.TabularInline):
    """دروس المقرر"""
    model = CurriculumLesson
    extra = 0
    fields = ['lesson_number', 'title', 'lesson_type', 'duration_minutes', 'is_active']
    show_change_link = True
    verbose_name = _('درس')
    verbose_name_plural = _('دروس المقرر')


class StudentCurriculumInline(admin.TabularInline):
    """طلاب المقرر"""
    model = StudentCurriculum
    extra = 0
    fields = ['student', 'sheikh', 'status', 'progress_display', 'start_date']
    raw_id_fields = ['student', 'sheikh']
    autocomplete_fields = ['student', 'sheikh']
    readonly_fields = ['progress_display']
    verbose_name = _('طالب مسجل')
    verbose_name_plural = _('الطلاب المسجلين')
    
    def progress_display(self, obj):
        return f"{obj.get_progress_percentage()}%"
    progress_display.short_description = 'نسبة التقدم'


class LessonReminderInline(admin.TabularInline):
    """تذكيرات الدروس"""
    model = LessonReminder
    extra = 0
    fields = ['lesson', 'scheduled_date', 'scheduled_time', 'reminder_sent', 'is_completed']
    raw_id_fields = ['lesson']
    autocomplete_fields = ['lesson']
    verbose_name = _('تذكير')
    verbose_name_plural = _('تذكيرات الدروس')


class QuoteNotificationInline(admin.TabularInline):
    """إشعارات الكلمات التحفيزية"""
    model = QuoteNotification
    extra = 0
    fields = ['student', 'is_read', 'created_at']
    raw_id_fields = ['student']
    autocomplete_fields = ['student']
    readonly_fields = ['created_at']
    verbose_name = _('إشعار')
    verbose_name_plural = _('الإشعارات المرسلة')


@admin.register(Curriculum)
class CurriculumAdmin(admin.ModelAdmin):
    """إدارة المقررات"""
    list_display = ['name', 'curriculum_type', 'duration_weeks', 'total_lessons_display', 
                   'target_juz_count_display', 'is_active', 'created_at']
    list_filter = ['curriculum_type', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [CurriculumLessonInline, StudentCurriculumInline]
    
    fieldsets = (
        ('معلومات أساسية', {
            'fields': ('name', 'description', 'curriculum_type', 'image', 'is_active')
        }),
        ('الهدف القرآني', {
            'fields': ('target_surah_from', 'target_surah_to', 'target_juz_from', 'target_juz_to')
        }),
        ('المدة والتنظيم', {
            'fields': ('duration_weeks', 'lessons_per_week', 'minutes_per_lesson')
        }),
        ('تواريخ', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def total_lessons_display(self, obj):
        return obj.total_lessons
    total_lessons_display.short_description = 'إجمالي الدروس'
    
    def target_juz_count_display(self, obj):
        return obj.target_juz_count
    target_juz_count_display.short_description = 'عدد الأجزاء'


@admin.register(CurriculumLesson)
class CurriculumLessonAdmin(admin.ModelAdmin):
    """إدارة دروس المقرر"""
    list_display = ['lesson_number', 'title', 'curriculum', 'lesson_type', 'duration_minutes', 'is_active']
    list_filter = ['lesson_type', 'is_active', 'curriculum']
    search_fields = ['title', 'description', 'curriculum__name']
    list_select_related = ['curriculum']
    raw_id_fields = ['curriculum', 'surah_from', 'surah_to']
    autocomplete_fields = ['curriculum', 'surah_from', 'surah_to']
    
    fieldsets = (
        ('معلومات أساسية', {
            'fields': ('curriculum', 'lesson_number', 'title', 'description', 'lesson_type', 'duration_minutes', 'is_active')
        }),
        ('المحتوى القرآني', {
            'fields': ('surah_from', 'ayah_from', 'surah_to', 'ayah_to')
        }),
        ('التفسير', {
            'fields': ('tafseer_content', 'tafseer_video_url')
        }),
        ('الأسبقية', {
            'fields': ('prerequisite_lessons',),
            'classes': ('collapse',)
        }),
    )
    filter_horizontal = ['prerequisite_lessons']


@admin.register(StudentCurriculum)
class StudentCurriculumAdmin(admin.ModelAdmin):
    """إدارة مقررات الطلاب"""
    list_display = ['student', 'curriculum', 'sheikh', 'status', 'progress_display', 'start_date', 'enable_reminders']
    list_filter = ['status', 'enable_reminders', 'created_at']
    search_fields = ['student__username', 'student__first_name', 'student__last_name', 'curriculum__name']
    raw_id_fields = ['student', 'curriculum', 'sheikh', 'current_lesson']
    autocomplete_fields = ['student', 'curriculum', 'sheikh', 'current_lesson']
    list_select_related = ['student', 'curriculum', 'sheikh']
    inlines = [LessonReminderInline]
    
    fieldsets = (
        ('معلومات أساسية', {
            'fields': ('student', 'curriculum', 'sheikh', 'status', 'current_lesson')
        }),
        ('التواريخ', {
            'fields': ('start_date', 'expected_end_date', 'actual_end_date')
        }),
        ('التنبيهات', {
            'fields': ('enable_reminders', 'reminder_time', 'timezone')
        }),
    )
    
    def progress_display(self, obj):
        return f"{obj.get_progress_percentage()}%"
    progress_display.short_description = 'نسبة التقدم'


@admin.register(MotivationalQuote)
class MotivationalQuoteAdmin(admin.ModelAdmin):
    """إدارة الكلمات التحفيزية"""
    list_display = ['title', 'category', 'is_scheduled', 'scheduled_date', 'is_published', 'view_count', 'is_active']
    list_filter = ['category', 'is_scheduled', 'is_published', 'is_active', 'created_at']
    search_fields = ['title', 'content', 'author']
    readonly_fields = ['view_count', 'published_at', 'created_at']
    inlines = [QuoteNotificationInline]
    
    fieldsets = (
        ('المحتوى', {
            'fields': ('title', 'content', 'category', 'author', 'source')
        }),
        ('الوسائط', {
            'fields': ('image', 'audio')
        }),
        ('الجدولة', {
            'fields': ('is_scheduled', 'scheduled_date', 'scheduled_time', 'timezone')
        }),
        ('التكرار', {
            'fields': ('is_recurring', 'recurring_days')
        }),
        ('الحالة', {
            'fields': ('is_published', 'published_at', 'view_count', 'is_active')
        }),
    )
    actions = ['publish_quotes']
    
    def publish_quotes(self, request, queryset):
        for quote in queryset:
            quote.publish()
        self.message_user(request, f"تم نشر {queryset.count()} كلمة تحفيزية")
    publish_quotes.short_description = 'نشر الكلمات المحددة'


@admin.register(QuoteNotification)
class QuoteNotificationAdmin(admin.ModelAdmin):
    """إدارة إشعارات الكلمات التحفيزية"""
    list_display = ['quote', 'student', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['quote__title', 'student__username', 'student__first_name']
    raw_id_fields = ['quote', 'student']
    autocomplete_fields = ['quote', 'student']
    readonly_fields = ['created_at']


@admin.register(TafseerLesson)
class TafseerLessonAdmin(admin.ModelAdmin):
    """إدارة دروس التفسير"""
    list_display = ['surah', 'ayah_from', 'ayah_to', 'title', 'is_scheduled', 'scheduled_date', 'is_published', 'is_active']
    list_filter = ['is_scheduled', 'is_published', 'is_active', 'recurring_type', 'created_at']
    search_fields = ['title', 'content', 'surah__name_arabic']
    raw_id_fields = ['surah']
    autocomplete_fields = ['surah']
    filter_horizontal = ['target_halaqat', 'target_curriculums']
    readonly_fields = ['view_count', 'published_at', 'created_at']
    
    fieldsets = (
        ('المحتوى', {
            'fields': ('surah', 'ayah_from', 'ayah_to', 'title', 'content', 'summary')
        }),
        ('الوسائط', {
            'fields': ('video_url', 'audio_url', 'pdf_file')
        }),
        ('الجدولة', {
            'fields': ('is_scheduled', 'scheduled_date', 'scheduled_time', 'timezone')
        }),
        ('التكرار', {
            'fields': ('is_recurring', 'recurring_type')
        }),
        ('المستهدفون', {
            'fields': ('target_halaqat', 'target_curriculums')
        }),
        ('الحالة', {
            'fields': ('is_published', 'published_at', 'view_count', 'is_active')
        }),
    )
    actions = ['publish_lessons']
    
    def publish_lessons(self, request, queryset):
        for lesson in queryset:
            lesson.publish()
        self.message_user(request, f"تم نشر {queryset.count()} درس تفسير")
    publish_lessons.short_description = 'نشر الدروس المحددة'


@admin.register(ScheduledNotification)
class ScheduledNotificationAdmin(admin.ModelAdmin):
    """إدارة الإشعارات المجدولة"""
    list_display = ['title', 'notification_type', 'scheduled_datetime', 'status', 'target_all_students', 'is_active']
    list_filter = ['notification_type', 'status', 'is_active', 'scheduled_datetime']
    search_fields = ['title', 'content']
    raw_id_fields = ['quote', 'tafseer', 'created_by']
    autocomplete_fields = ['quote', 'tafseer']
    filter_horizontal = ['target_halaqat', 'target_students']
    readonly_fields = ['sent_at', 'created_at']
    
    fieldsets = (
        ('المحتوى', {
            'fields': ('title', 'content', 'notification_type')
        }),
        ('الربط بالمحتوى', {
            'fields': ('quote', 'tafseer')
        }),
        ('الجدولة', {
            'fields': ('scheduled_datetime', 'timezone')
        }),
        ('المستهدفون', {
            'fields': ('target_all_students', 'target_halaqat', 'target_students')
        }),
        ('التكرار', {
            'fields': ('is_recurring', 'recurring_cron')
        }),
        ('الحالة', {
            'fields': ('status', 'sent_at', 'error_message', 'is_active')
        }),
    )
    actions = ['resend_notifications', 'cancel_notifications']
    
    def resend_notifications(self, request, queryset):
        queryset.update(status=ScheduledNotification.Status.PENDING, error_message='')
        self.message_user(request, f"تم إعادة تعيين {queryset.count()} إشعار للإرسال")
    resend_notifications.short_description = 'إعادة إرسال الإشعارات المحددة'
    
    def cancel_notifications(self, request, queryset):
        queryset.update(status=ScheduledNotification.Status.CANCELLED)
        self.message_user(request, f"تم إلغاء {queryset.count()} إشعار")
    cancel_notifications.short_description = 'إلغاء الإشعارات المحددة'


@admin.register(LessonReminder)
class LessonReminderAdmin(admin.ModelAdmin):
    """إدارة تذكيرات الدروس"""
    list_display = ['student_curriculum', 'lesson', 'scheduled_date', 'scheduled_time', 'reminder_sent', 'is_completed']
    list_filter = ['reminder_sent', 'is_completed', 'scheduled_date']
    search_fields = ['student_curriculum__student__username', 'lesson__title']
    raw_id_fields = ['student_curriculum', 'lesson']
    autocomplete_fields = ['student_curriculum', 'lesson']
    readonly_fields = ['reminder_sent_at', 'completed_at', 'created_at']
