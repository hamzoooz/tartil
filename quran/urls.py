"""
Quran URLs
مسارات القرآن الكريم
"""
from django.urls import path
from . import views

app_name = 'quran'

urlpatterns = [
    path('', views.index, name='index'),
    path('surah/<int:surah_number>/', views.surah_view, name='surah'),
    path('page/<int:page_number>/', views.page_view, name='page'),
    path('juz/<int:juz_number>/', views.juz_view, name='juz'),
    path('search/', views.search, name='search'),

    # API
    path('api/surah/<int:surah_number>/', views.api_surah, name='api_surah'),
    path('api/ayah/<int:surah_number>/<int:ayah_number>/', views.api_ayah, name='api_ayah'),
]
