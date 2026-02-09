"""
نماذج التقارير والشهادات
Forms for Reports and Certificates
"""
from django import forms
from django.utils.translation import gettext_lazy as _
from .models import CertificateTemplate, Certificate, StudentReport, BulkCertificateGeneration
from accounts.models import CustomUser
from halaqat.models import Halaqa


class CertificateTemplateForm(forms.ModelForm):
    """نموذج إنشاء/تعديل قالب شهادة"""
    
    class Meta:
        model = CertificateTemplate
        fields = [
            'name', 'description', 'template_image', 'is_active',
            'default_title', 'default_description',
            # إعدادات الاسم
            'name_font_size', 'name_font_color', 
            'name_position_x', 'name_position_y', 'name_font_family',
            # إعدادات الدرجة
            'degree_font_size', 'degree_font_color',
            'degree_position_x', 'degree_position_y', 'degree_font_family',
            # إعدادات التاريخ
            'date_font_size', 'date_font_color',
            'date_position_x', 'date_position_y', 'date_font_family',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'template_image': forms.FileInput(attrs={'class': 'form-control'}),
            'default_title': forms.TextInput(attrs={'class': 'form-control'}),
            'default_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            # إعدادات الاسم
            'name_font_size': forms.NumberInput(attrs={'class': 'form-control', 'min': 10, 'max': 200}),
            'name_font_color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'name_position_x': forms.NumberInput(attrs={'class': 'form-control'}),
            'name_position_y': forms.NumberInput(attrs={'class': 'form-control'}),
            'name_font_family': forms.TextInput(attrs={'class': 'form-control'}),
            # إعدادات الدرجة
            'degree_font_size': forms.NumberInput(attrs={'class': 'form-control', 'min': 10, 'max': 200}),
            'degree_font_color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'degree_position_x': forms.NumberInput(attrs={'class': 'form-control'}),
            'degree_position_y': forms.NumberInput(attrs={'class': 'form-control'}),
            'degree_font_family': forms.TextInput(attrs={'class': 'form-control'}),
            # إعدادات التاريخ
            'date_font_size': forms.NumberInput(attrs={'class': 'form-control', 'min': 10, 'max': 200}),
            'date_font_color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'date_position_x': forms.NumberInput(attrs={'class': 'form-control'}),
            'date_position_y': forms.NumberInput(attrs={'class': 'form-control'}),
            'date_font_family': forms.TextInput(attrs={'class': 'form-control'}),
        }


class CertificateForm(forms.ModelForm):
    """نموذج إنشاء شهادة فردية"""
    
    # حقول اختيار الطالب
    student = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(user_type='student'),
        label=_('الطالب'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    # حقول التخصيص
    customize_positions = forms.BooleanField(
        label=_('تخصيص المواقع'),
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    class Meta:
        model = Certificate
        fields = [
            'template', 'student', 'custom_name', 
            'degree_title', 'degree_description', 'issue_date',
            'name_position_x_override', 'name_position_y_override',
            'degree_position_x_override', 'degree_position_y_override',
        ]
        widgets = {
            'template': forms.Select(attrs={'class': 'form-select'}),
            'custom_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('اتركه فارغاً لاستخدام اسم الطالب')
            }),
            'degree_title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('مثال: شهادة إتمام حفظ القرآن الكريم')
            }),
            'degree_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('وصف الإنجاز المحقق')
            }),
            'issue_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'name_position_x_override': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': _('X')
            }),
            'name_position_y_override': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': _('Y')
            }),
            'degree_position_x_override': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': _('X')
            }),
            'degree_position_y_override': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': _('Y')
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # تفعيل حقول المواقع فقط إذا تم اختيار التخصيص
        self.fields['name_position_x_override'].required = False
        self.fields['name_position_y_override'].required = False
        self.fields['degree_position_x_override'].required = False
        self.fields['degree_position_y_override'].required = False


class StudentReportForm(forms.ModelForm):
    """نموذج إنشاء تقرير طالب"""
    
    student = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(user_type='student'),
        label=_('الطالب'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    auto_generate = forms.BooleanField(
        label=_('توليد الإحصائيات تلقائياً من البيانات'),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    class Meta:
        model = StudentReport
        fields = [
            'student', 'report_period', 'start_date', 'end_date',
            'total_sessions', 'total_recitations', 'total_pages_memorized',
            'total_pages_reviewed', 'average_grade', 'attendance_rate',
            'total_errors', 'tajweed_errors', 'memorization_errors',
            'general_evaluation', 'recommendations',
        ]
        widgets = {
            'report_period': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'total_sessions': forms.NumberInput(attrs={'class': 'form-control'}),
            'total_recitations': forms.NumberInput(attrs={'class': 'form-control'}),
            'total_pages_memorized': forms.NumberInput(attrs={'class': 'form-control'}),
            'total_pages_reviewed': forms.NumberInput(attrs={'class': 'form-control'}),
            'average_grade': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'attendance_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'total_errors': forms.NumberInput(attrs={'class': 'form-control'}),
            'tajweed_errors': forms.NumberInput(attrs={'class': 'form-control'}),
            'memorization_errors': forms.NumberInput(attrs={'class': 'form-control'}),
            'general_evaluation': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'recommendations': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError(_('تاريخ البداية يجب أن يكون قبل تاريخ النهاية'))
        
        return cleaned_data


class BulkCertificateForm(forms.ModelForm):
    """نموذج توليد شهادات بالجملة"""
    
    class Meta:
        model = BulkCertificateGeneration
        fields = [
            'template', 'halaqa', 'degree_title', 'degree_description',
            'issue_date', 'min_grade', 'min_attendance_rate'
        ]
        widgets = {
            'template': forms.Select(attrs={'class': 'form-select'}),
            'halaqa': forms.Select(attrs={'class': 'form-select'}),
            'degree_title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('عنوان الشهادة للجميع')
            }),
            'degree_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('وصف الإنجاز')
            }),
            'issue_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'min_grade': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'min': 0,
                'max': 100
            }),
            'min_attendance_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': 0,
                'max': 100
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['halaqa'].required = False
        self.fields['halaqa'].queryset = Halaqa.objects.filter(status='active')


class CertificatePreviewForm(forms.Form):
    """نموذج معاينة الشهادة"""
    
    template = forms.ModelChoiceField(
        queryset=CertificateTemplate.objects.filter(is_active=True),
        label=_('القالب'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    preview_name = forms.CharField(
        label=_('الاسم للمعاينة'),
        initial=_('أحمد محمد'),
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    preview_degree = forms.CharField(
        label=_('الدرجة للمعاينة'),
        initial=_('شهادة إتمام حفظ القرآن الكريم'),
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    preview_date = forms.DateField(
        label=_('التاريخ للمعاينة'),
        initial=forms.fields.DateField().initial,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )


class ReportFilterForm(forms.Form):
    """نموذج تصفية التقارير"""
    
    student = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(user_type='student'),
        label=_('الطالب'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    period = forms.ChoiceField(
        choices=StudentReport.ReportPeriod.choices,
        label=_('الفترة'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    start_date = forms.DateField(
        label=_('من تاريخ'),
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    end_date = forms.DateField(
        label=_('إلى تاريخ'),
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
