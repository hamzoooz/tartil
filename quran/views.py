"""
Quran Views
صفحات القرآن الكريم
"""
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import Surah, Ayah, Juz, QuranPage


def index(request):
    """فهرس السور"""
    surahs = Surah.objects.all()
    return render(request, 'quran/index.html', {'surahs': surahs})


def surah_view(request, surah_number):
    """عرض سورة"""
    surah = get_object_or_404(Surah, number=surah_number)
    ayat = Ayah.objects.filter(surah=surah).order_by('number')

    # السورة السابقة والتالية
    prev_surah = Surah.objects.filter(number=surah_number - 1).first()
    next_surah = Surah.objects.filter(number=surah_number + 1).first()

    context = {
        'surah': surah,
        'ayat': ayat,
        'prev_surah': prev_surah,
        'next_surah': next_surah,
    }
    return render(request, 'quran/surah.html', context)


def page_view(request, page_number):
    """عرض صفحة من المصحف"""
    ayat = Ayah.objects.filter(page=page_number).order_by('surah__number', 'number')
    page_obj = QuranPage.objects.filter(number=page_number).first()

    context = {
        'page_number': page_number,
        'page': page_obj,
        'ayat': ayat,
    }
    return render(request, 'quran/page.html', context)


def juz_view(request, juz_number):
    """عرض جزء"""
    juz = get_object_or_404(Juz, number=juz_number)
    ayat = Ayah.objects.filter(juz=juz_number).order_by('surah__number', 'number')

    context = {
        'juz': juz,
        'ayat': ayat,
    }
    return render(request, 'quran/juz.html', context)


def search(request):
    """البحث في القرآن"""
    query = request.GET.get('q', '')
    results = []

    if query and len(query) >= 2:
        results = Ayah.objects.filter(
            text_uthmani__icontains=query
        ).select_related('surah')[:50]

    context = {
        'query': query,
        'results': results,
    }
    return render(request, 'quran/search.html', context)


# API Views
def api_surah(request, surah_number):
    """API: بيانات السورة"""
    surah = get_object_or_404(Surah, number=surah_number)
    ayat = list(Ayah.objects.filter(surah=surah).values(
        'number', 'text_uthmani', 'page', 'juz'
    ))

    return JsonResponse({
        'surah': {
            'number': surah.number,
            'name_arabic': surah.name_arabic,
            'name_english': surah.name_english,
            'total_ayat': surah.total_ayat,
            'revelation_type': surah.revelation_type,
        },
        'ayat': ayat
    })


def api_ayah(request, surah_number, ayah_number):
    """API: بيانات آية"""
    ayah = get_object_or_404(
        Ayah,
        surah__number=surah_number,
        number=ayah_number
    )

    return JsonResponse({
        'surah': ayah.surah.number,
        'surah_name': ayah.surah.name_arabic,
        'ayah': ayah.number,
        'text': ayah.text_uthmani,
        'page': ayah.page,
        'juz': ayah.juz,
    })
