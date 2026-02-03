"""
Recitation URLs
مسارات التسميع
"""
from django.urls import path
from . import views

app_name = 'recitation'

urlpatterns = [
    path('my-records/', views.my_records, name='my_records'),
    path('record/<int:pk>/', views.record_detail, name='record_detail'),
    path('progress/', views.progress, name='progress'),
    path('evaluate/', views.evaluate, name='evaluate'),
    path('create/<int:session_id>/', views.create_record, name='create_record'),
    path('goals/', views.daily_goals, name='daily_goals'),
]
