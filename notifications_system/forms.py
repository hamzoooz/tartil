"""
نماذج النماذج (Forms) لنظام النشر
Forms for Notification System
"""
from django import forms
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import datetime

from .models import ScheduledNotification, NotificationTemplate


class ScheduledNotificationForm(forms.ModelForm):
    """نموذج إنشاء/تعديل إشعار مجدول"""
    
    # حقول إضافية للتاريخ والوقت
    schedule_date = forms.DateField(
        label=_('تاريخ الإرسال'),
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control form-control-dashboard',
        }),
        required=True
    )
    
    schedule_time = forms.TimeField(
        label=_('وقت الإرسال'),
        widget=forms.TimeInput(attrs={
            'type': 'time',
            'class': 'form-control form-control-dashboard',
        }),
        required=True
    )
    
    class Meta:
        model = ScheduledNotification
        fields = [
            'title',
            'content_type',
            'template',
            'message',
            'image',
            'link',
            'lesson',
            'tafseer',
            'timezone',
            'recurrence_type',
            'recurrence_days',
            'recurrence_end_date',
            'target_type',
            'target_halaqa',
            'target_course',
            'target_users',
            'is_enabled',
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control form-control-dashboard',
                'placeholder': _('عنوان الإشعار'),
            }),
            'content_type': forms.Select(attrs={
                'class': 'form-select form-control-dashboard',
            }),
            'template': forms.Select(attrs={
                'class': 'form-select form-control-dashboard',
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control form-control-dashboard',
                'rows': 5,
                'placeholder': _('محتوى الرسالة...'),
            }),
            'link': forms.URLInput(attrs={
                'class': 'form-control form-control-dashboard',
                'placeholder': 'https://...',
            }),
            'timezone': forms.TextInput(attrs={
                'class': 'form-control form-control-dashboard',
            }),
            'recurrence_type': forms.Select(attrs={
                'class': 'form-select form-control-dashboard',
            }),
            'recurrence_days': forms.CheckboxSelectMultiple(),
            'recurrence_end_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control form-control-dashboard',
            }),
            'target_type': forms.Select(attrs={
                'class': 'form-select form-control-dashboard',
            }),
            'target_halaqa': forms.Select(attrs={
                'class': 'form-select form-control-dashboard',
            }),
            'target_course': forms.Select(attrs={
                'class': 'form-select form-control-dashboard',
            }),
            'target_users': forms.SelectMultiple(attrs={
                'class': 'form-select form-control-dashboard',
                'size': 5,
            }),
            'is_enabled': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # تهيئة حقول التاريخ والوقت إذا كان هناك instance
        if self.instance and self.instance.pk and self.instance.scheduled_datetime:
            self.fields['schedule_date'].initial = self.instance.scheduled_datetime.date()
            self.fields['schedule_time'].initial = self.instance.scheduled_datetime.time()
        else:
            # قيم افتراضية
            now = timezone.now()
            self.fields['schedule_date'].initial = now.date()
            self.fields['schedule_time'].initial = now.strftime('%H:%M')
        
        # تصفية القوالب حسب النوع
        self.fields['template'].queryset = NotificationTemplate.objects.filter(
            is_active=True
        )
        self.fields['template'].required = False
        
        # تعديل queryset للمستخدمين
        from accounts.models import CustomUser
        self.fields['target_users'].queryset = CustomUser.objects.filter(
            is_active=True
        ).order_by('first_name', 'last_name')
        
        # تعديل queryset للحلقات
        from halaqat.models import Halaqa
        self.fields['target_halaqa'].queryset = Halaqa.objects.filter(
            status='active'
        )
        
        # تعديل queryset للمقررات
        from courses.models import Curriculum
        self.fields['target_course'].queryset = Curriculum.objects.filter(
            is_active=True
        )
    
    def clean(self):
        cleaned_data = super().clean()
        
        # دمج التاريخ والوقت
        schedule_date = cleaned_data.get('schedule_date')
        schedule_time = cleaned_data.get('schedule_time')
        
        if schedule_date and schedule_time:
            scheduled_datetime = datetime.combine(schedule_date, schedule_time)
            # تحويل إلى timezone-aware
            tz = cleaned_data.get('timezone', 'Asia/Riyadh')
            import pytz
            try:
                timezone_obj = pytz.timezone(tz)
                scheduled_datetime = timezone_obj.localize(scheduled_datetime)
                cleaned_data['scheduled_datetime'] = scheduled_datetime
            except pytz.exceptions.UnknownTimeZoneError:
                self.add_error('timezone', _('المنطقة الزمنية غير صالحة'))
        
        # التحقق من صحة المستهدفين
        target_type = cleaned_data.get('target_type')
        target_halaqa = cleaned_data.get('target_halaqa')
        target_course = cleaned_data.get('target_course')
        target_users = cleaned_data.get('target_users')
        
        if target_type == ScheduledNotification.TargetType.HALAQA and not target_halaqa:
            self.add_error('target_halaqa', _('يرجى اختيار الحلقة'))
        
        if target_type == ScheduledNotification.TargetType.COURSE and not target_course:
            self.add_error('target_course', _('يرجى اختيار المقرر'))
        
        if target_type == ScheduledNotification.TargetType.SPECIFIC_USERS and not target_users:
            self.add_error('target_users', _('يرجى اختيار مستخدم واحد على الأقل'))
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # تعيين التاريخ والوقت
        if 'scheduled_datetime' in self.cleaned_data:
            instance.scheduled_datetime = self.cleaned_data['scheduled_datetime']
        
        # تعيين المنشئ
        if self.user and not instance.pk:
            instance.created_by = self.user
        
        if commit:
            instance.save()
            self.save_m2m()
        
        return instance


class NotificationTemplateForm(forms.ModelForm):
    """نموذج إنشاء/تعديل قالب إشعار"""
    
    class Meta:
        model = NotificationTemplate
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control form-control-dashboard',
            }),
            'content_type': forms.Select(attrs={
                'class': 'form-select form-control-dashboard',
            }),
            'title_template': forms.TextInput(attrs={
                'class': 'form-control form-control-dashboard',
            }),
            'message_template': forms.Textarea(attrs={
                'class': 'form-control form-control-dashboard',
                'rows': 5,
            }),
            'link': forms.URLInput(attrs={
                'class': 'form-control form-control-dashboard',
            }),
            'available_variables': forms.HiddenInput(),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }


class QuickSendForm(forms.Form):
    """نموذج الإرسال السريع"""
    
    content_type = forms.ChoiceField(
        label=_('نوع المحتوى'),
        choices=NotificationTemplate.ContentType.choices,
        widget=forms.Select(attrs={
            'class': 'form-select form-control-dashboard',
        })
    )
    
    title = forms.CharField(
        label=_('العنوان'),
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-dashboard',
        })
    )
    
    message = forms.CharField(
        label=_('الرسالة'),
        widget=forms.Textarea(attrs={
            'class': 'form-control form-control-dashboard',
            'rows': 4,
        })
    )
    
    target_type = forms.ChoiceField(
        label=_('المستهدفون'),
        choices=ScheduledNotification.TargetType.choices,
        widget=forms.Select(attrs={
            'class': 'form-select form-control-dashboard',
        })
    )
    
    target_halaqa = forms.ModelChoiceField(
        label=_('الحلقة'),
        queryset=None,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select form-control-dashboard',
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from halaqat.models import Halaqa
        self.fields['target_halaqa'].queryset = Halaqa.objects.filter(status='active')


class NotificationFilterForm(forms.Form):
    """نموذج تصفية الإشعارات"""
    
    status = forms.ChoiceField(
        label=_('الحالة'),
        choices=[('', _('الكل'))] + list(ScheduledNotification.Status.choices),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select form-control-dashboard',
        })
    )
    
    content_type = forms.ChoiceField(
        label=_('نوع المحتوى'),
        choices=[('', _('الكل'))] + list(NotificationTemplate.ContentType.choices),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select form-control-dashboard',
        })
    )
    
    target_type = forms.ChoiceField(
        label=_('نوع المستهدفين'),
        choices=[('', _('الكل'))] + list(ScheduledNotification.TargetType.choices),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select form-control-dashboard',
        })
    )
    
    date_from = forms.DateField(
        label=_('من تاريخ'),
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control form-control-dashboard',
        })
    )
    
    date_to = forms.DateField(
        label=_('إلى تاريخ'),
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control form-control-dashboard',
        })
    )
    
    search = forms.CharField(
        label=_('بحث'),
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-dashboard',
            'placeholder': _('ابحث في العنوان...'),
        })
    )
