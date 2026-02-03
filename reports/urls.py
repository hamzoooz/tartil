"""
Reports URLs
مسارات التقارير
"""
from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('admin/', views.admin_reports, name='admin'),
    path('sheikh/', views.sheikh_reports, name='sheikh'),
    path('student/', views.student_report, name='student_self'),
    path('student/<int:student_id>/', views.student_report, name='student'),
]
