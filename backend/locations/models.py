from django.contrib.gis.db import models
from django.conf import settings


class Category(models.Model):
    """Категорія для групування локацій (наприклад: Природа, Інфраструктура, Небезпека)."""
    name = models.CharField(max_length=100, verbose_name='Назва')
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True, verbose_name='Опис')
    color = models.CharField(max_length=7, default='#3B82F6', verbose_name='Колір на карті')
    icon = models.CharField(max_length=50, blank=True, verbose_name='Іконка (назва)')

    class Meta:
        verbose_name = 'Категорія'
        verbose_name_plural = 'Категорії'
        ordering = ['name']

    def __str__(self):
        return self.name


class Tag(models.Model):
    """Теги для локацій."""
    name = models.CharField(max_length=50, unique=True, verbose_name='Тег')

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Location(models.Model):
    """
    Головна модель — геоточка з метаданими.
    Використовує PostGIS PointField для зберігання координат.
    """
    # Основна інформація
    title = models.CharField(max_length=200, verbose_name='Назва')
    description = models.TextField(blank=True, verbose_name='Опис')

    # Геодані — PointField зберігає (longitude, latitude) в SRID=4326 (WGS84)
    point = models.PointField(srid=4326, verbose_name='Координати')

    # Зв'язки
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='locations',
        verbose_name='Власник'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='locations',
        verbose_name='Категорія'
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name='locations', verbose_name='Теги')

    # Налаштування видимості
    is_public = models.BooleanField(default=True, verbose_name='Публічна')

    # Метадані
    address = models.CharField(max_length=500, blank=True, verbose_name='Адреса')
    altitude = models.FloatField(null=True, blank=True, verbose_name='Висота (м)')
    image = models.ImageField(upload_to='locations/', null=True, blank=True, verbose_name='Фото')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Створено')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Оновлено')

    class Meta:
        verbose_name = 'Локація'
        verbose_name_plural = 'Локації'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def latitude(self):
        return self.point.y

    @property
    def longitude(self):
        return self.point.x