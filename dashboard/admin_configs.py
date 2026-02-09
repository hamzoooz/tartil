"""
Enhanced Admin Configurations for all apps
تكوينات إدارية محسنة لجميع التطبيقات
"""
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.utils.html import format_html
from django.db.models import Count, Sum, Avg
from django.utils.translation import gettext_lazy as _

from accounts.models import CustomUser, StudentProfile, SheikhProfile, Notification, ActivityLog
from halaqat.models import Halaqa, Session, Attendance, HalaqaEnrollment, Course
from recitation.models import RecitationRecord, RecitationError, MemorizationProgress, DailyGoal
from courses.models import Curriculum, CurriculumLesson, StudentCurriculum, MotivationalQuote, TafseerLesson
from gamification.models import Badge, PointsLog, Streak, Achievement, StudentBadge, StudentAchievement
from reports.models import Certificate, StudentReport, CertificateTemplate
from quran.models import Surah, Ayah, Juz

User = get_user_model()

# Unregister existing models to register with enhanced configs
try:
    admin.site.unregister(CustomUser)
except admin.sites.NotRegistered:
    pass

try:
    admin.site.unregister(StudentProfile)
except admin.sites.NotRegistered:
    pass

try:
    admin.site.unregister(SheikhProfile)
except admin.sites.NotRegistered:
    pass


# ==================== ACCOUNTS ADMIN ====================

class StudentProfileInline(admin.StackedInline):
    model = StudentProfile
    can_delete = False
    verbose_name_plural = 'ملف الطالب'


class SheikhProfileInline(admin.StackedInline):
    model = SheikhProfile
    can_delete = False
    verbose_name_plural = 'ملف الشيخ'


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'username', 'get_full_name', 'email', 'user_type_colored',
        'phone', 'is_active', 'date_joined', 'last_login_display'
    ]
    list_filter = ['user_type', 'is_active', 'gender', 'date_joined']
    search_fields = ['username', 'first_name', 'last_name', 'email', 'phone']
    list_editable = ['is_active']
    ordering = ['-date_joined']
    date_hierarchy = 'date_joined'
    
    fieldsets = (
        (_('معلومات تسجيل الدخول'), {
            'fields': ('username', 'password')
        }),
        (_('معلومات شخصية'), {
            'fields': ('first_name', 'last_name', 'email', 'phone', 'gender', 'date_of_birth')
        }),
        (_('الملف الشخصي'), {
            'fields': ('profile_image', 'bio', 'country', 'city')
        }),
        (_('الصلاحيات'), {
            'fields': ('user_type', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        (_('تواريخ مهمة'), {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [StudentProfileInline, SheikhProfileInline]
    
    def user_type_colored(self, obj):
        colors = {
            'admin': 'danger',
            'sheikh': 'warning',
            'student': 'primary',
            'parent': 'secondary'
        }
        return format_html(
            '<span class="badge badge-{}" style="padding: 5px 10px;">{}</span>',
            colors.get(obj.user_type, 'secondary'),
            obj.get_user_type_display()
        )
    user_type_colored.short_description = _('نوع المستخدم')
    
    def last_login_display(self, obj):
        if obj.last_login:
            return obj.last_login.strftime('%Y-%m-%d %H:%M')
        return '-'
    last_login_display.short_description = _('آخر دخول')


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'parent', 'total_memorized_juz', 'total_memorized_pages',
        'memorization_percentage', 'total_points', 'memorization_start_date'
    ]
    list_filter = ['memorization_start_date', 'total_memorized_juz']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']
    raw_id_fields = ['user', 'parent']
    date_hierarchy = 'memorization_start_date'
    
    def memorization_percentage(self, obj):
        return format_html(
            '<div class="progress" style="width: 100px;">'
            '<div class="progress-bar" style="width: {}%">{}%</div></div>',
            obj.memorization_percentage, obj.memorization_percentage
        )
    memorization_percentage.short_description = _('نسبة الحفظ')


@admin.register(SheikhProfile)
class SheikhProfileAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'specialization', 'years_of_experience', 'max_students',
        'rating', 'total_sessions', 'hourly_rate'
    ]
    list_filter = ['specialization', 'years_of_experience']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']
    raw_id_fields = ['user']


# ==================== HALAQAT ADMIN ====================

class HalaqaEnrollmentInline(admin.TabularInline):
    model = HalaqaEnrollment
    extra = 0
    raw_id_fields = ['student']
    autocomplete_fields = ['student']


class SessionInline(admin.TabularInline):
    model = Session
    extra = 0
    fields = ['date', 'start_time', 'status']


@admin.register(Halaqa)
class HalaqaAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'sheikh', 'course', 'enrolled_count', 'max_students',
        'status_colored', 'schedule_days', 'created_at'
    ]
    list_filter = ['status', 'course', 'created_at']
    search_fields = ['name', 'sheikh__username', 'sheikh__first_name']
    raw_id_fields = ['sheikh', 'course']
    date_hierarchy = 'created_at'
    inlines = [HalaqaEnrollmentInline, SessionInline]
    
    def status_colored(self, obj):
        colors = {
            'active': 'success',
            'paused': 'warning',
            'completed': 'info',
            'cancelled': 'secondary'
        }
        return format_html(
            '<span class="badge badge-{}" style="padding: 5px 10px;">{}</span>',
            colors.get(obj.status, 'secondary'),
            obj.get_status_display()
        )
    status_colored.short_description = _('الحالة')


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = [
        'halaqa', 'date', 'start_time', 'status_colored',
        'duration_actual', 'attendees_count'
    ]
    list_filter = ['status', 'date', 'halaqa']
    search_fields = ['halaqa__name', 'notes']
    raw_id_fields = ['halaqa']
    date_hierarchy = 'date'
    
    def status_colored(self, obj):
        colors = {
            'scheduled': 'info',
            'in_progress': 'warning',
            'completed': 'success',
            'cancelled': 'danger',
            'postponed': 'secondary'
        }
        return format_html(
            '<span class="badge badge-{}" style="padding: 5px 10px;">{}</span>',
            colors.get(obj.status, 'secondary'),
            obj.get_status_display()
        )
    status_colored.short_description = _('الحالة')
    
    def attendees_count(self, obj):
        return obj.attendances.filter(status='present').count()
    attendees_count.short_description = _('الحاضرون')


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = [
        'student', 'session', 'status_colored', 'check_in_time', 'check_out_time'
    ]
    list_filter = ['status', 'session__date']
    search_fields = ['student__username', 'student__first_name', 'session__halaqa__name']
    raw_id_fields = ['student', 'session']
    date_hierarchy = 'session__date'
    
    def status_colored(self, obj):
        colors = {
            'present': 'success',
            'absent': 'danger',
            'excused': 'info',
            'late': 'warning'
        }
        return format_html(
            '<span class="badge badge-{}" style="padding: 5px 10px;">{}</span>',
            colors.get(obj.status, 'secondary'),
            obj.get_status_display()
        )
    status_colored.short_description = _('الحالة')


# ==================== RECITATION ADMIN ====================

class RecitationErrorInline(admin.TabularInline):
    model = RecitationError
    extra = 0
    raw_id_fields = ['surah']


@admin.register(RecitationRecord)
class RecitationRecordAdmin(admin.ModelAdmin):
    list_display = [
        'student', 'surah_range', 'recitation_type_colored', 'grade_colored',
        'total_errors', 'grade_level', 'created_at'
    ]
    list_filter = ['recitation_type', 'grade_level', 'created_at', 'surah_start']
    search_fields = ['student__username', 'student__first_name', 'notes']
    raw_id_fields = ['student', 'session', 'surah_start', 'surah_end']
    date_hierarchy = 'created_at'
    inlines = [RecitationErrorInline]
    
    def surah_range(self, obj):
        if obj.surah_start == obj.surah_end:
            return f"{obj.surah_start.name_arabic} ({obj.ayah_start}-{obj.ayah_end})"
        return f"{obj.surah_start.name_arabic} ({obj.ayah_start}) - {obj.surah_end.name_arabic} ({obj.ayah_end})"
    surah_range.short_description = _('النطاق')
    
    def recitation_type_colored(self, obj):
        colors = {
            'new': 'primary',
            'review': 'success',
            'tilawa': 'info'
        }
        return format_html(
            '<span class="badge badge-{}" style="padding: 5px 10px;">{}</span>',
            colors.get(obj.recitation_type, 'secondary'),
            obj.get_recitation_type_display()
        )
    recitation_type_colored.short_description = _('النوع')
    
    def grade_colored(self, obj):
        if obj.grade >= 90:
            color = 'success'
        elif obj.grade >= 70:
            color = 'warning'
        else:
            color = 'danger'
        return format_html(
            '<span class="badge badge-{}" style="padding: 5px 10px;">{}%</span>',
            color, obj.grade
        )
    grade_colored.short_description = _('الدرجة')


@admin.register(RecitationError)
class RecitationErrorAdmin(admin.ModelAdmin):
    list_display = [
        'record', 'surah', 'ayah', 'error_type_colored', 'severity_colored'
    ]
    list_filter = ['error_type', 'severity', 'created_at']
    search_fields = ['word_text', 'notes', 'record__student__username']
    raw_id_fields = ['record', 'surah']
    
    def error_type_colored(self, obj):
        return format_html(
            '<span class="badge badge-info" style="padding: 5px 10px;">{}</span>',
            obj.get_error_type_display()
        )
    error_type_colored.short_description = _('نوع الخطأ')
    
    def severity_colored(self, obj):
        colors = {
            'minor': 'secondary',
            'major': 'warning',
            'critical': 'danger'
        }
        return format_html(
            '<span class="badge badge-{}" style="padding: 5px 10px;">{}</span>',
            colors.get(obj.severity, 'secondary'),
            obj.get_severity_display()
        )
    severity_colored.short_description = _('الشدة')


# ==================== COURSES ADMIN ====================

class CurriculumLessonInline(admin.TabularInline):
    model = CurriculumLesson
    extra = 1
    raw_id_fields = ['surah_from', 'surah_to']


@admin.register(Curriculum)
class CurriculumAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'curriculum_type', 'total_lessons', 'duration_weeks',
        'is_active', 'created_at'
    ]
    list_filter = ['curriculum_type', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    inlines = [CurriculumLessonInline]


@admin.register(TafseerLesson)
class TafseerLessonAdmin(admin.ModelAdmin):
    list_display = ['title', 'surah', 'ayah_from', 'ayah_to', 'is_published', 'view_count']
    list_filter = ['is_published', 'created_at']
    search_fields = ['title', 'content', 'surah__name_arabic']
    raw_id_fields = ['surah']
    filter_horizontal = ['target_halaqat', 'target_curriculums']


# ==================== GAMIFICATION ADMIN ====================

@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ['name', 'badge_type', 'level', 'points_reward', 'is_active']
    list_filter = ['badge_type', 'level', 'is_active']
    search_fields = ['name', 'description']


@admin.register(PointsLog)
class PointsLogAdmin(admin.ModelAdmin):
    list_display = ['student', 'points', 'points_type', 'reason', 'created_at']
    list_filter = ['points_type', 'created_at']
    search_fields = ['student__username', 'reason']
    raw_id_fields = ['student']
    date_hierarchy = 'created_at'


@admin.register(Streak)
class StreakAdmin(admin.ModelAdmin):
    list_display = ['student', 'current_streak', 'longest_streak', 'total_active_days', 'last_activity_date']
    list_filter = ['last_activity_date']
    search_fields = ['student__username', 'student__first_name']
    raw_id_fields = ['student']


# ==================== REPORTS ADMIN ====================

@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ['student', 'template', 'certificate_number', 'status', 'issue_date']
    list_filter = ['status', 'issue_date', 'template']
    search_fields = ['student__username', 'certificate_number', 'custom_name']
    raw_id_fields = ['student', 'template']
    date_hierarchy = 'issue_date'


@admin.register(StudentReport)
class StudentReportAdmin(admin.ModelAdmin):
    list_display = [
        'student', 'report_period', 'start_date', 'end_date',
        'average_grade', 'attendance_rate'
    ]
    list_filter = ['report_period', 'created_at']
    search_fields = ['student__username', 'student__first_name']
    raw_id_fields = ['student']
    date_hierarchy = 'created_at'


# ==================== QURAN ADMIN ====================

class AyahInline(admin.TabularInline):
    model = Ayah
    extra = 0
    fields = ['number', 'text_simple', 'page', 'juz']


@admin.register(Surah)
class SurahAdmin(admin.ModelAdmin):
    list_display = [
        'number', 'name_arabic', 'name_english', 'total_ayat',
        'revelation_type', 'total_pages'
    ]
    list_filter = ['revelation_type']
    search_fields = ['name_arabic', 'name_english', 'name_transliteration']
    ordering = ['number']
    inlines = [AyahInline]


@admin.register(Juz)
class JuzAdmin(admin.ModelAdmin):
    list_display = ['number', 'start_surah', 'start_ayah', 'end_surah', 'end_ayah']
    search_fields = ['name']
    raw_id_fields = ['start_surah', 'end_surah']


# ==================== CUSTOMIZE DEFAULT ADMIN ====================

# Override the default admin site title
admin.site.site_header = 'دورات القرآن - لوحة التحكم المتقدمة'
admin.site.site_title = 'دورات القرآن'
admin.site.index_title = 'نظرة عامة'

# Add custom CSS to admin
admin.site.enable_nav_sidebar = True
