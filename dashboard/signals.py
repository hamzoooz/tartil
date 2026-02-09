"""
إشارات لوحة التحكم - Dashboard Signals
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.core.cache import cache

User = get_user_model()


@receiver(post_save, sender=User)
def clear_user_cache(sender, instance, **kwargs):
    """مسح الكاش عند تعديل المستخدم"""
    cache.delete('dashboard_stats')
    cache.delete(f'user_stats_{instance.id}')
