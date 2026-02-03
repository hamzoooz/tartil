"""
إدارة نماذج الحلقات
"""
from django.contrib import admin
from .models import Course, Halaqa, HalaqaEnrollment, Session, Attendance


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    """إدارة المسارات"""
    list_display = ['name', 'course_type', 'duration_months', 'price', 'is_active']
    list_filter = ['course_type', 'is_active']
    search_fields = ['name', 'description']


@admin.register(Halaqa)
class HalaqaAdmin(admin.ModelAdmin):
    """إدارة الحلقات"""
    list_display = ['name', 'sheikh', 'course', 'max_students', 'enrolled_count',
                   'status', 'schedule_time']
    list_filter = ['status', 'course', 'is_private']
    search_fields = ['name', 'sheikh__first_name', 'sheikh__last_name']
    raw_id_fields = ['sheikh', 'course']
    date_hierarchy = 'created_at'

    def enrolled_count(self, obj):
        return obj.enrolled_count
    enrolled_count.short_description = 'عدد المسجلين'


@admin.register(HalaqaEnrollment)
class HalaqaEnrollmentAdmin(admin.ModelAdmin):
    """إدارة تسجيلات الحلقات"""
    list_display = ['student', 'halaqa', 'enrolled_date', 'status']
    list_filter = ['status', 'enrolled_date', 'halaqa']
    search_fields = ['student__first_name', 'student__last_name', 'halaqa__name']
    raw_id_fields = ['student', 'halaqa']
    date_hierarchy = 'enrolled_date'


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    """إدارة الجلسات"""
    list_display = ['halaqa', 'date', 'start_time', 'status', 'duration_actual']
    list_filter = ['status', 'date', 'halaqa']
    search_fields = ['halaqa__name', 'notes']
    raw_id_fields = ['halaqa']
    date_hierarchy = 'date'

    def duration_actual(self, obj):
        return f"{obj.duration_actual} دقيقة" if obj.duration_actual else "-"
    duration_actual.short_description = 'المدة الفعلية'


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    """إدارة الحضور"""
    list_display = ['student', 'session', 'status', 'check_in_time']
    list_filter = ['status', 'session__date']
    search_fields = ['student__first_name', 'student__last_name']
    raw_id_fields = ['student', 'session']
