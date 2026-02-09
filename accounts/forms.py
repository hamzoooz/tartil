"""
Accounts Forms
نماذج الحسابات
"""
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser


class UserRegistrationForm(UserCreationForm):
    """نموذج تسجيل مستخدم جديد"""

    first_name = forms.CharField(
        max_length=30,
        required=True,
        label='الاسم الأول'
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        label='الاسم الأخير'
    )
    email = forms.EmailField(
        required=True,
        label='البريد الإلكتروني'
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        label='رقم الجوال'
    )
    user_type = forms.ChoiceField(
        choices=[
            ('student', 'طالب'),
            ('sheikh', 'شيخ / معلم'),
            ('parent', 'ولي أمر'),
        ],
        label='نوع الحساب'
    )
    gender = forms.ChoiceField(
        choices=[
            ('', '-- اختر --'),
            ('male', 'ذكر'),
            ('female', 'أنثى'),
        ],
        required=False,
        label='الجنس'
    )

    class Meta:
        model = CustomUser
        fields = ['username', 'first_name', 'last_name', 'email', 'phone',
                  'user_type', 'gender', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.phone = self.cleaned_data.get('phone', '')
        user.user_type = self.cleaned_data['user_type']
        user.gender = self.cleaned_data.get('gender', '')

        if commit:
            user.save()
        return user


class UserUpdateForm(forms.ModelForm):
    """نموذج تحديث بيانات المستخدم"""

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'phone',
                  'bio', 'country', 'city', 'profile_image']
        labels = {
            'first_name': 'الاسم الأول',
            'last_name': 'الاسم الأخير',
            'email': 'البريد الإلكتروني',
            'phone': 'رقم الجوال',
            'bio': 'نبذة شخصية',
            'country': 'الدولة',
            'city': 'المدينة',
            'profile_image': 'الصورة الشخصية',
        }
