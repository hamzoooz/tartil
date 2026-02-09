"""
Gamification URLs
مسارات التلعيب
"""
from django.urls import path
from . import views

app_name = 'gamification'

urlpatterns = [
    path('badges/', views.badges, name='badges'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('points/', views.points_history, name='points'),
    path('achievements/', views.achievements, name='achievements'),
    path('streak/', views.streak_info, name='streak'),
]
