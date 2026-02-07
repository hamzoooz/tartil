"""
Forms for Advanced Admin Dashboard
"""
from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.forms import UserCreationForm

from accounts.models import CustomUser, StudentProfile, SheikhProfile
from halaqat.models import Halaqa, Session, Attendance
from recitation.models import RecitationRecord, RecitationError
from courses.models import Curriculum, CurriculumLesson
from .models import DashboardSettings, BulkAction

User = get_user_model()


class DashboardSettingsForm(forms.ModelForm):
    """نموذج إعدادات لوحة التحكم"""
    
    class Meta:
        model = DashboardSettings
        fields = ['theme', 'items_per_page', 'sidebar_collapsed', 
                  'email_notifications', 'push_notifications']
        widgets = {
            'theme': forms.Select(attrs={'class': 'form-select'}),
            'items_per_page': forms.Select(attrs={'class': 'form-select'}),
            'sidebar_collapsed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'email_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'push_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class UserQuickForm(forms.ModelForm):
    """نموذج سريع لإضافة مستخدم"""
    password = forms.CharField(
        label=_('كلمة المرور'),
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False,
        help_text=_('اتركه فارغاً لتوليد كلمة مرور عشوائية')
    )
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 
                  'user_type', 'phone', 'gender', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'user_type': forms.Select(attrs={'class': 'form-select'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def save(self, commit=True):
        user = super().save(commit=False)
        if self.cleaned_data['password']:
            user.set_password(self.cleaned_data['password'])
        else:
            # توليد كلمة مرور عشوائية
            import secrets
            password = secrets.token_urlsafe(12)
            user.set_password(password)
            self.generated_password = password
        
        if commit:
            user.save()
        return user


class StudentProfileForm(forms.ModelForm):
    """نموذج ملف الطالب"""
    
    class Meta:
        model = StudentProfile
        fields = ['current_surah', 'current_ayah', 'total_memorized_pages',
                  'total_memorized_juz', 'memorization_start_date', 
                  'target_completion_date', 'notes']
        widgets = {
            'current_surah': forms.NumberInput(attrs={'class': 'form-control'}),
            'current_ayah': forms.NumberInput(attrs={'class': 'form-control'}),
            'total_memorized_pages': forms.NumberInput(attrs={'class': 'form-control'}),
            'total_memorized_juz': forms.NumberInput(attrs={'class': 'form-control'}),
            'memorization_start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'target_completion_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class SheikhProfileForm(forms.ModelForm):
    """نموذج ملف الشيخ"""
    
    class Meta:
        model = SheikhProfile
        fields = ['specialization', 'ijazah_info', 'years_of_experience',
                  'max_students', 'available_days', 'available_times', 'hourly_rate']
        widgets = {
            'specialization': forms.Select(attrs={'class': 'form-select'}),
            'ijazah_info': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'years_of_experience': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_students': forms.NumberInput(attrs={'class': 'form-control'}),
            'available_days': forms.TextInput(attrs={'class': 'form-control'}),
            'available_times': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'hourly_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


class HalaqaQuickForm(forms.ModelForm):
    """نموذج سريع لإضافة حلقة"""
    
    class Meta:
        model = Halaqa
        fields = ['name', 'course', 'sheikh', 'description', 'max_students',
                  'schedule_days', 'schedule_time', 'duration_minutes', 'status']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'course': forms.Select(attrs={'class': 'form-select'}),
            'sheikh': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'max_students': forms.NumberInput(attrs={'class': 'form-control'}),
            'schedule_days': forms.TextInput(attrs={'class': 'form-control'}),
            'schedule_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'duration_minutes': forms.NumberInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }


class SessionQuickForm(forms.ModelForm):
    """نموذج سريع لإضافة جلسة"""
    
    class Meta:
        model = Session
        fields = ['halaqa', 'date', 'start_time', 'end_time', 'meet_link', 'status']
        widgets = {
            'halaqa': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'meet_link': forms.URLInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }


class AttendanceQuickForm(forms.ModelForm):
    """نموذج سريع لتسجيل الحضور"""
    
    class Meta:
        model = Attendance
        fields = ['student', 'session', 'status', 'notes']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-select'}),
            'session': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.TextInput(attrs={'class': 'form-control'}),
        }


class RecitationQuickForm(forms.ModelForm):
    """نموذج سريع لتسجيل التسميع"""
    
    class Meta:
        model = RecitationRecord
        fields = ['student', 'session', 'surah_start', 'ayah_start', 
                  'surah_end', 'ayah_end', 'recitation_type', 'grade', 'notes']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-select'}),
            'session': forms.Select(attrs={'class': 'form-select'}),
            'surah_start': forms.Select(attrs={'class': 'form-select'}),
            'ayah_start': forms.NumberInput(attrs={'class': 'form-control'}),
            'surah_end': forms.Select(attrs={'class': 'form-select'}),
            'ayah_end': forms.NumberInput(attrs={'class': 'form-control'}),
            'recitation_type': forms.Select(attrs={'class': 'form-select'}),
            'grade': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0', 'max': '100'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class RecitationErrorForm(forms.ModelForm):
    """نموذج تسجيل خطأ في التسميع"""
    
    class Meta:
        model = RecitationError
        fields = ['record', 'surah', 'ayah', 'word_index', 'word_text',
                  'error_type', 'severity', 'notes']
        widgets = {
            'record': forms.Select(attrs={'class': 'form-select'}),
            'surah': forms.Select(attrs={'class': 'form-select'}),
            'ayah': forms.NumberInput(attrs={'class': 'form-control'}),
            'word_index': forms.NumberInput(attrs={'class': 'form-control'}),
            'word_text': forms.TextInput(attrs={'class': 'form-control'}),
            'error_type': forms.Select(attrs={'class': 'form-select'}),
            'severity': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class CurriculumQuickForm(forms.ModelForm):
    """نموذج سريع لإضافة مقرر"""
    
    class Meta:
        model = Curriculum
        fields = ['name', 'description', 'curriculum_type', 'duration_weeks',
                  'lessons_per_week', 'minutes_per_lesson', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'curriculum_type': forms.Select(attrs={'class': 'form-select'}),
            'duration_weeks': forms.NumberInput(attrs={'class': 'form-control'}),
            'lessons_per_week': forms.NumberInput(attrs={'class': 'form-control'}),
            'minutes_per_lesson': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class DateRangeFilterForm(forms.Form):
    """نموذج تصفية حسب التاريخ"""
    date_from = forms.DateField(
        label=_('من تاريخ'),
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    date_to = forms.DateField(
        label=_('إلى تاريخ'),
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )


class BulkActionForm(forms.ModelForm):
    """نموذج إنشاء إجراء جماعي"""
    
    class Meta:
        model = BulkAction
        fields = ['name', 'description', 'model_name', 'action_type', 
                  'field_updates', 'filter_conditions']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'model_name': forms.Select(attrs={'class': 'form-select'}),
            'action_type': forms.Select(attrs={'class': 'form-select'}),
            'field_updates': forms.HiddenInput(),
            'filter_conditions': forms.HiddenInput(),
        }


class ExportDataForm(forms.Form):
    """نموذج تصدير البيانات"""
    MODEL_CHOICES = [
        ('users', _('المستخدمين')),
        ('students', _('الطلاب')),
        ('sheikhs', _('المشايخ')),
        ('halaqat', _('الحلقات')),
        ('sessions', _('الجلسات')),
        ('attendance', _('الحضور')),
        ('recitations', _('التسميعات')),
        ('errors', _('الأخطاء')),
        ('curriculums', _('المقررات')),
        ('points', _('النقاط')),
        ('certificates', _('الشهادات')),
    ]
    
    FORMAT_CHOICES = [
        ('csv', _('CSV')),
        ('excel', _('Excel')),
        ('json', _('JSON')),
        ('pdf', _('PDF')),
    ]
    
    model = forms.ChoiceField(
        label=_('النموذج'),
        choices=MODEL_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    format = forms.ChoiceField(
        label=_('الصيغة'),
        choices=FORMAT_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    date_from = forms.DateField(
        label=_('من تاريخ'),
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    date_to = forms.DateField(
        label=_('إلى تاريخ'),
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    include_inactive = forms.BooleanField(
        label=_('تضمين غير النشطين'),
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


class ImportDataForm(forms.Form):
    """نموذج استيراد البيانات"""
    MODEL_CHOICES = [
        ('users', _('المستخدمين')),
        ('students', _('الطلاب')),
        ('halaqat', _('الحلقات')),
        ('sessions', _('الجلسات')),
        ('attendance', _('الحضور')),
        ('recitations', _('التسميعات')),
    ]
    
    model = forms.ChoiceField(
        label=_('النموذج'),
        choices=MODEL_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    file = forms.FileField(
        label=_('الملف'),
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.csv,.xlsx,.json'})
    )
    skip_validation = forms.BooleanField(
        label=_('تخطي التحقق'),
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_('تحذير: قد يؤدي إلى استيراد بيانات غير صحيحة')
    )
