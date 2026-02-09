"""
Halaqat URLs
مسارات الحلقات
"""
from django.urls import path
from . import views

app_name = 'halaqat'

urlpatterns = [
    path('', views.halaqa_list, name='list'),
    path('<int:pk>/', views.halaqa_detail, name='detail'),
    path('<int:pk>/enroll/', views.enroll, name='enroll'),
    path('my/', views.my_halaqat, name='my_halaqat'),
    path('manage/', views.manage_halaqat, name='manage'),
    path('create/', views.create_halaqa, name='create'),
    path('sessions/', views.sessions_list, name='sessions'),
    path('all/', views.all_halaqat, name='all'),
]
