"""
إدارة نماذج الحلقات
"""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Course, Halaqa, HalaqaEnrollment, Session, Attendance


class HalaqaEnrollmentInline(admin.TabularInline):
    """تسجيلات الطلاب في الحلقة"""
    model = HalaqaEnrollment
    extra = 0
    fields = ['student', 'enrolled_date', 'status', 'notes']
    raw_id_fields = ['student']
    autocomplete_fields = ['student']
    verbose_name = _('تسجيل طالب')
    verbose_name_plural = _('تسجيلات الطلاب')


class SessionInline(admin.TabularInline):
    """الجلسات المتعلقة بالحلقة"""
    model = Session
    extra = 0
    fields = ['date', 'start_time', 'end_time', 'status', 'meet_link']
    show_change_link = True
    verbose_name = _('جلسة')
    verbose_name_plural = _('الجلسات')


class AttendanceInline(admin.TabularInline):
    """سجل الحضور للجلسة"""
    model = Attendance
    extra = 0
    fields = ['student', 'status', 'check_in_time', 'check_out_time', 'notes']
    raw_id_fields = ['student']
    autocomplete_fields = ['student']
    verbose_name = _('حضور')
    verbose_name_plural = _('سجل الحضور')


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    """إدارة المسارات"""
    list_display = ['name', 'course_type', 'duration_months', 'price', 'is_active', 'created_at']
    list_filter = ['course_type', 'is_active']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at']


@admin.register(Halaqa)
class HalaqaAdmin(admin.ModelAdmin):
    """إدارة الحلقات"""
    list_display = ['name', 'sheikh', 'course', 'max_students', 'enrolled_count_display',
                   'status', 'schedule_time', 'is_private']
    list_filter = ['status', 'course', 'is_private']
    search_fields = ['name', 'sheikh__first_name', 'sheikh__last_name', 'sheikh__username']
    raw_id_fields = ['sheikh', 'course']
    autocomplete_fields = ['sheikh', 'course']
    date_hierarchy = 'created_at'
    inlines = [HalaqaEnrollmentInline, SessionInline]
    
    fieldsets = (
        ('معلومات أساسية', {
            'fields': ('name', 'description', 'course', 'sheikh')
        }),
        ('الجدولة', {
            'fields': ('schedule_days', 'schedule_time', 'duration_minutes')
        }),
        ('الإعدادات', {
            'fields': ('max_students', 'meet_link', 'is_private', 'status')
        }),
    )

    def enrolled_count_display(self, obj):
        return obj.enrolled_count
    enrolled_count_display.short_description = 'عدد المسجلين'


@admin.register(HalaqaEnrollment)
class HalaqaEnrollmentAdmin(admin.ModelAdmin):
    """إدارة تسجيلات الحلقات"""
    list_display = ['student', 'halaqa', 'enrolled_date', 'status']
    list_filter = ['status', 'enrolled_date', 'halaqa']
    search_fields = ['student__first_name', 'student__last_name', 'student__username', 'halaqa__name']
    raw_id_fields = ['student', 'halaqa']
    autocomplete_fields = ['student', 'halaqa']
    date_hierarchy = 'enrolled_date'


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    """إدارة الجلسات"""
    list_display = ['halaqa', 'date', 'start_time', 'status', 'duration_actual_display', 'attendance_count']
    list_filter = ['status', 'date', 'halaqa']
    search_fields = ['halaqa__name', 'notes']
    raw_id_fields = ['halaqa']
    autocomplete_fields = ['halaqa']
    date_hierarchy = 'date'
    inlines = [AttendanceInline]
    
    fieldsets = (
        ('معلومات الجلسة', {
            'fields': ('halaqa', 'date', 'start_time', 'end_time', 'meet_link')
        }),
        ('الحالة', {
            'fields': ('status', 'notes')
        }),
        ('الأوقات الفعلية', {
            'fields': ('actual_start', 'actual_end'),
            'classes': ('collapse',)
        }),
    )

    def duration_actual_display(self, obj):
        return f"{obj.duration_actual} دقيقة" if obj.duration_actual else "-"
    duration_actual_display.short_description = 'المدة الفعلية'
    
    def attendance_count(self, obj):
        return obj.attendances.count()
    attendance_count.short_description = 'عدد الحضور'


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    """إدارة الحضور"""
    list_display = ['student', 'session', 'session_halaqa', 'status', 'check_in_time', 'session_date']
    list_filter = ['status', 'session__date', 'session__halaqa']
    search_fields = ['student__first_name', 'student__last_name', 'student__username', 'notes']
    raw_id_fields = ['student', 'session']
    autocomplete_fields = ['student', 'session']
    
    def session_halaqa(self, obj):
        return obj.session.halaqa.name
    session_halaqa.short_description = 'الحلقة'
    
    def session_date(self, obj):
        return obj.session.date
    session_date.short_description = 'تاريخ الجلسة'
    session_date.admin_order_field = 'session__date'
