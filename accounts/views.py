"""
Accounts Views
صفحات الحسابات
"""
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from .models import CustomUser, StudentProfile, SheikhProfile
from .forms import UserRegistrationForm, UserUpdateForm


def login_view(request):
    """تسجيل الدخول"""
    if request.user.is_authenticated:
        return redirect('core:dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f'مرحباً {user.get_full_name() or user.username}!')
            next_url = request.GET.get('next', 'core:dashboard')
            return redirect(next_url)
        else:
            messages.error(request, 'اسم المستخدم أو كلمة المرور غير صحيحة')

    return render(request, 'accounts/login.html')


def logout_view(request):
    """تسجيل الخروج"""
    logout(request)
    messages.success(request, 'تم تسجيل الخروج بنجاح')
    return redirect('core:home')


def register(request):
    """إنشاء حساب جديد"""
    if request.user.is_authenticated:
        return redirect('core:dashboard')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()

            # إنشاء ملف شخصي حسب نوع المستخدم
            if user.user_type == 'student':
                StudentProfile.objects.create(user=user)
            elif user.user_type == 'sheikh':
                SheikhProfile.objects.create(user=user)

            login(request, user)
            messages.success(request, 'تم إنشاء حسابك بنجاح! مرحباً بك في ترتيل')
            return redirect('core:dashboard')
    else:
        form = UserRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


@login_required
def profile(request):
    """الملف الشخصي"""
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.phone = request.POST.get('phone', user.phone)
        user.country = request.POST.get('country', user.country)
        user.city = request.POST.get('city', user.city)
        user.bio = request.POST.get('bio', user.bio)

        if 'profile_image' in request.FILES:
            user.profile_image = request.FILES['profile_image']

        user.save()
        messages.success(request, 'تم تحديث الملف الشخصي بنجاح')

    return render(request, 'accounts/profile.html')


@login_required
def settings_view(request):
    """الإعدادات"""
    return render(request, 'accounts/settings.html')


@login_required
def change_password(request):
    """تغيير كلمة المرور"""
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password1 = request.POST.get('new_password1')
        new_password2 = request.POST.get('new_password2')

        if not request.user.check_password(old_password):
            messages.error(request, 'كلمة المرور الحالية غير صحيحة')
        elif new_password1 != new_password2:
            messages.error(request, 'كلمات المرور الجديدة غير متطابقة')
        elif len(new_password1) < 8:
            messages.error(request, 'كلمة المرور يجب أن تكون 8 أحرف على الأقل')
        else:
            request.user.set_password(new_password1)
            request.user.save()
            update_session_auth_hash(request, request.user)
            messages.success(request, 'تم تغيير كلمة المرور بنجاح')

    return redirect('accounts:settings')
