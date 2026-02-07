"""
Admin configuration for Reports app
"""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import CertificateTemplate, Certificate, StudentReport, BulkCertificateGeneration


class CertificateInline(admin.TabularInline):
    """الشهادات الممنوحة للطالب"""
    model = Certificate
    extra = 0
    fields = ['certificate_number', 'template', 'issue_date', 'status']
    raw_id_fields = ['template']
    autocomplete_fields = ['template']
    show_change_link = True
    verbose_name = _('شهادة')
    verbose_name_plural = _('الشهادات')


class StudentReportInline(admin.TabularInline):
    """تقارير الطالب"""
    model = StudentReport
    extra = 0
    fields = ['report_period', 'start_date', 'end_date', 'average_grade', 'attendance_rate']
    show_change_link = True
    verbose_name = _('تقرير')
    verbose_name_plural = _('التقارير')


@admin.register(CertificateTemplate)
class CertificateTemplateAdmin(admin.ModelAdmin):
    """إدارة قوالب الشهادات"""
    list_display = ['name', 'is_active', 'created_at', 'updated_at', 'certificates_count']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('معلومات أساسية', {
            'fields': ('name', 'description', 'template_image', 'is_active')
        }),
        ('إعدادات خط الاسم', {
            'fields': ('name_font_size', 'name_font_color', 'name_position_x', 'name_position_y', 'name_font_family')
        }),
        ('إعدادات خط الدرجة', {
            'fields': ('degree_font_size', 'degree_font_color', 'degree_position_x', 'degree_position_y', 'degree_font_family')
        }),
        ('إعدادات خط التاريخ', {
            'fields': ('date_font_size', 'date_font_color', 'date_position_x', 'date_position_y', 'date_font_family')
        }),
        ('النصوص الافتراضية', {
            'fields': ('default_title', 'default_description')
        }),
        ('التواريخ', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def certificates_count(self, obj):
        return obj.certificates.count()
    certificates_count.short_description = 'عدد الشهادات'


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    """إدارة الشهادات"""
    list_display = ['certificate_number', 'student', 'template', 'degree_title', 'issue_date', 'status', 'created_at']
    list_filter = ['status', 'template', 'issue_date']
    search_fields = ['certificate_number', 'student__username', 'student__first_name', 'student__last_name', 'degree_title']
    readonly_fields = ['certificate_number', 'created_at', 'updated_at']
    raw_id_fields = ['student', 'template']
    autocomplete_fields = ['student', 'template']
    date_hierarchy = 'issue_date'
    
    fieldsets = (
        ('معلومات أساسية', {
            'fields': ('template', 'student', 'certificate_number')
        }),
        ('البيانات المخصصة', {
            'fields': ('custom_name', 'degree_title', 'degree_description', 'issue_date')
        }),
        ('الحالة والملف', {
            'fields': ('status', 'generated_file')
        }),
        ('تخصيص المواضع (اختياري)', {
            'fields': ('name_position_x_override', 'name_position_y_override', 
                      'degree_position_x_override', 'degree_position_y_override'),
            'classes': ('collapse',)
        }),
        ('التواريخ', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(StudentReport)
class StudentReportAdmin(admin.ModelAdmin):
    """إدارة تقارير الطلاب"""
    list_display = ['student', 'report_period', 'start_date', 'end_date', 'average_grade', 
                   'attendance_rate', 'total_sessions', 'created_at']
    list_filter = ['report_period', 'start_date']
    search_fields = ['student__username', 'student__first_name', 'student__last_name']
    readonly_fields = ['created_at']
    raw_id_fields = ['student']
    autocomplete_fields = ['student']
    date_hierarchy = 'start_date'
    
    fieldsets = (
        ('معلومات أساسية', {
            'fields': ('student', 'report_period', 'start_date', 'end_date')
        }),
        ('إحصائيات الحفظ', {
            'fields': ('total_sessions', 'total_recitations', 'total_pages_memorized', 'total_pages_reviewed')
        }),
        ('التقييم', {
            'fields': ('average_grade', 'attendance_rate')
        }),
        ('إحصائيات الأخطاء', {
            'fields': ('total_errors', 'tajweed_errors', 'memorization_errors')
        }),
        ('التقييم العام', {
            'fields': ('general_evaluation', 'recommendations')
        }),
        ('البيانات التفصيلية', {
            'fields': ('detailed_data',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['generate_statistics_action']
    
    def generate_statistics_action(self, request, queryset):
        for report in queryset:
            report.generate_statistics()
        self.message_user(request, f"تم توليد الإحصائيات لـ {queryset.count()} تقرير")
    generate_statistics_action.short_description = 'توليد الإحصائيات للتقارير المحددة'


@admin.register(BulkCertificateGeneration)
class BulkCertificateGenerationAdmin(admin.ModelAdmin):
    """إدارة توليد الشهادات بالجملة"""
    list_display = ['template', 'halaqa', 'degree_title', 'generated_count', 'min_grade', 'created_at']
    list_filter = ['template', 'created_at']
    readonly_fields = ['generated_count', 'created_at']
    raw_id_fields = ['halaqa', 'created_by']
    autocomplete_fields = ['halaqa']
    
    fieldsets = (
        ('معلومات أساسية', {
            'fields': ('template', 'halaqa')
        }),
        ('بيانات الشهادة', {
            'fields': ('degree_title', 'degree_description', 'issue_date')
        }),
        ('معايير التصفية', {
            'fields': ('min_grade', 'min_attendance_rate')
        }),
        ('النتيجة', {
            'fields': ('generated_count', 'created_at', 'created_by')
        }),
    )
    
    actions = ['generate_certificates_action']
    
    def generate_certificates_action(self, request, queryset):
        for bulk_gen in queryset:
            count = bulk_gen.generate_certificates()
        self.message_user(request, f"تم توليد الشهادات")
    generate_certificates_action.short_description = 'توليد الشهادات للعناصر المحددة'
