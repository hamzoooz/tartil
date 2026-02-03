"""
Gamification Views
صفحات التلعيب
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from .models import Badge, StudentBadge, PointsLog, Streak, Achievement, StudentAchievement, Leaderboard


@login_required
def badges(request):
    """صفحة الأوسمة"""
    # جميع الأوسمة المتاحة
    all_badges = Badge.objects.filter(is_active=True)

    # أوسمة المستخدم
    user_badges = StudentBadge.objects.filter(
        student=request.user
    ).select_related('badge')
    earned_badge_ids = user_badges.values_list('badge_id', flat=True)

    context = {
        'all_badges': all_badges,
        'user_badges': user_badges,
        'earned_badge_ids': list(earned_badge_ids),
    }
    return render(request, 'gamification/badges.html', context)


@login_required
def leaderboard(request):
    """لوحة المتصدرين"""
    from accounts.models import CustomUser, StudentProfile

    # أفضل 50 طالب حسب النقاط
    top_students = StudentProfile.objects.select_related('user').order_by(
        '-total_points'
    )[:50]

    # ترتيب المستخدم الحالي
    user_rank = None
    if request.user.is_student:
        try:
            user_profile = request.user.student_profile
            user_rank = StudentProfile.objects.filter(
                total_points__gt=user_profile.total_points
            ).count() + 1
        except:
            pass

    context = {
        'top_students': top_students,
        'user_rank': user_rank,
    }
    return render(request, 'gamification/leaderboard.html', context)


@login_required
def points_history(request):
    """سجل النقاط"""
    logs = PointsLog.objects.filter(student=request.user).order_by('-created_at')

    total_points = logs.aggregate(total=Sum('points'))['total'] or 0

    context = {
        'logs': logs,
        'total_points': total_points,
    }
    return render(request, 'gamification/points_history.html', context)


@login_required
def achievements(request):
    """الإنجازات"""
    all_achievements = Achievement.objects.filter(is_active=True)

    # إنجازات المستخدم
    user_achievements = StudentAchievement.objects.filter(
        student=request.user
    ).select_related('achievement')

    # تحويل لقاموس للوصول السريع
    user_achievement_map = {ua.achievement_id: ua for ua in user_achievements}

    context = {
        'all_achievements': all_achievements,
        'user_achievement_map': user_achievement_map,
    }
    return render(request, 'gamification/achievements.html', context)


@login_required
def streak_info(request):
    """معلومات المواظبة"""
    try:
        streak = request.user.streak
    except Streak.DoesNotExist:
        streak = Streak.objects.create(student=request.user)

    context = {
        'streak': streak,
    }
    return render(request, 'gamification/streak.html', context)
