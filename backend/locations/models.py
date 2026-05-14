from django.contrib.gis.db import models
from django.conf import settings

# Import OutboxEvent to register with Django
from .outbox import OutboxEvent, OutboxPublisher


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


class LocationManager(models.Manager):
    """Кастомний менеджер який приховує soft-deleted записи."""
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class Location(models.Model):
    """
    Головна модель — геоточка з метаданими.
    Використовує PostGIS PointField для зберігання координат.
    Реалізує Soft Delete (is_deleted замість фізичного видалення).
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

    # Soft Delete — архітектурний патерн
    is_deleted = models.BooleanField(default=False, verbose_name='Видалено')
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name='Видалено о')

    # Метадані
    address = models.CharField(max_length=500, blank=True, verbose_name='Адреса')
    altitude = models.FloatField(null=True, blank=True, verbose_name='Висота (м)')
    image = models.ImageField(upload_to='locations/', null=True, blank=True, verbose_name='Фото')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Створено')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Оновлено')

    # Менеджери
    objects = LocationManager()  # Default — без видалених
    all_objects = models.Manager()  # Всі записи (для адміна/відновлення)

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

    def soft_delete(self):
        """Soft delete — не видаляє з БД, а помічає як видалений."""
        from django.utils import timezone
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at'])

    def restore(self):
        """Відновлення видаленої локації."""
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=['is_deleted', 'deleted_at'])


class LocationComment(models.Model):
    """Коментар до локації."""
    location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Локація'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='location_comments',
        verbose_name='Автор'
    )
    text = models.TextField(verbose_name='Текст коментаря')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Створено')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Оновлено')

    class Meta:
        verbose_name = 'Коментар'
        verbose_name_plural = 'Коментарі'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.email}: {self.text[:50]}'


# Import OutboxEvent після визначення всіх моделей
from .outbox import OutboxEvent, OutboxPublisher