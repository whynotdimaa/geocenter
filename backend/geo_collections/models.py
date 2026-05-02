from django.db import models
from django.conf import settings
import uuid


class Collection(models.Model):
    """
    Колекція — іменована група локацій.
    Може бути публічною (видима всім) або приватною (тільки власник і запрошені).
    """
    name = models.CharField(max_length=200, verbose_name='Назва')
    description = models.TextField(blank=True, verbose_name='Опис')
    cover_image = models.ImageField(
        upload_to='geo_collections/', null=True, blank=True, verbose_name='Обкладинка'
    )

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='collections',
        verbose_name='Власник'
    )
    locations = models.ManyToManyField(
        'locations.Location',
        blank=True,
        related_name='collections',
        verbose_name='Локації'
    )

    is_public = models.BooleanField(default=False, verbose_name='Публічна')

    # Унікальний токен для посилання-запрошення
    invite_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Створено')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Оновлено')

    class Meta:
        verbose_name = 'Колекція'
        verbose_name_plural = 'Колекції'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} ({self.owner.email})'

    @property
    def locations_count(self):
        return self.locations.count()

    @property
    def members_count(self):
        return self.members.count()


class CollectionMember(models.Model):
    """
    Проміжна модель — права доступу конкретного користувача до колекції.
    Ролі: viewer (тільки перегляд) або editor (може додавати/видаляти локації).
    """
    ROLE_VIEWER = 'viewer'
    ROLE_EDITOR = 'editor'
    ROLE_CHOICES = [
        (ROLE_VIEWER, 'Переглядач'),
        (ROLE_EDITOR, 'Редактор'),
    ]

    collection = models.ForeignKey(
        Collection,
        on_delete=models.CASCADE,
        related_name='members',
        verbose_name='Колекція'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='collection_memberships',
        verbose_name='Користувач'
    )
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default=ROLE_VIEWER,
        verbose_name='Роль'
    )
    joined_at = models.DateTimeField(auto_now_add=True, verbose_name='Приєднався')

    class Meta:
        verbose_name = 'Учасник колекції'
        verbose_name_plural = 'Учасники колекцій'
        # Один юзер — одна роль в одній колекції
        unique_together = ('collection', 'user')

    def __str__(self):
        return f'{self.user.email} → {self.collection.name} [{self.role}]'
