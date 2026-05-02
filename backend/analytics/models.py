from django.db import models
from django.conf import settings


class LocationView(models.Model):
    """
    Лог перегляду локації. Записується кожен раз коли юзер відкриває деталі.
    Використовується для статистики популярності.
    """
    location = models.ForeignKey(
        'locations.Location',
        on_delete=models.CASCADE,
        related_name='views',
        verbose_name='Локація'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='location_views',
        verbose_name='Користувач'
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name='IP адреса')
    viewed_at = models.DateTimeField(auto_now_add=True, verbose_name='Переглянуто')

    class Meta:
        verbose_name = 'Перегляд локації'
        verbose_name_plural = 'Перегляди локацій'
        ordering = ['-viewed_at']

    def __str__(self):
        return f'{self.location.title} — {self.viewed_at.strftime("%Y-%m-%d %H:%M")}'


class ClusterResult(models.Model):
    """
    Збережений результат кластеризації K-Means.
    Зберігає параметри запиту і JSON з результатами щоб не рахувати повторно.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cluster_results',
        verbose_name='Користувач'
    )
    n_clusters = models.IntegerField(verbose_name='Кількість кластерів')
    # JSON зі списком кластерів: [{center: [lng, lat], points: [...], size: N}]
    result_json = models.JSONField(verbose_name='Результат кластеризації')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Створено')

    class Meta:
        verbose_name = 'Результат кластеризації'
        verbose_name_plural = 'Результати кластеризації'
        ordering = ['-created_at']

    def __str__(self):
        return f'Кластеризація {self.n_clusters} кластерів — {self.user.email}'