"""
Transactional Outbox Pattern implementation.

Гарантує, що події будуть доставлені іншим мікросервісам
навіть якщо брокер повідомлень тимчасово недоступний.

Патерн:
1. Записуємо бізнес-дані в БД (транзакція)
2. В тій же транзакції — записуємо подію в outbox таблицю
3. Окремий процес читає outbox і відправляє події
"""
import uuid
from typing import Any, Dict

from django.db import models
from django.utils import timezone


class OutboxEvent(models.Model):
    """
    Таблиця Outbox — зберігає події для надійної доставки.
    
    Статуси:
    - pending: чекає відправки
    - processed: успішно відправлено
    - failed: помилка після всіх ретрайів
    """
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PROCESSED = 'processed', 'Processed'
        FAILED = 'failed', 'Failed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Ідентифікація агрегату (сутності)
    aggregate_type = models.CharField(max_length=100, verbose_name='Тип сутності')
    aggregate_id = models.CharField(max_length=100, verbose_name='ID сутності')
    
    # Тип події та payload
    event_type = models.CharField(max_length=100, verbose_name='Тип події')
    payload = models.JSONField(verbose_name='Дані події')
    
    # Метадані
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Створено')
    processed_at = models.DateTimeField(null=True, blank=True, verbose_name='Відправлено')
    retry_count = models.PositiveIntegerField(default=0, verbose_name='Кількість спроб')
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name='Статус'
    )
    error_message = models.TextField(blank=True, verbose_name='Помилка')

    class Meta:
        verbose_name = 'Outbox подія'
        verbose_name_plural = 'Outbox події'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['aggregate_type', 'aggregate_id']),
        ]

    def __str__(self):
        return f"{self.event_type} [{self.status}]"


class OutboxPublisher:
    """
    Helper для публікації подій в Outbox.
    
    Використання:
        with transaction.atomic():
            location.save()
            OutboxPublisher.publish(
                aggregate_type='Location',
                aggregate_id=str(location.id),
                event_type='LocationCreated',
                payload={'title': location.title, 'lat': location.latitude}
            )
    """
    
    @staticmethod
    def publish(
        aggregate_type: str,
        aggregate_id: str,
        event_type: str,
        payload: Dict[str, Any]
    ) -> OutboxEvent:
        """
        Створює подію в outbox таблиці.
        
        Важливо: викликати всередині transaction.atomic()!
        """
        return OutboxEvent.objects.create(
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            event_type=event_type,
            payload=payload
        )
    
    @staticmethod
    def publish_location_created(location) -> OutboxEvent:
        """Подія: локацію створено."""
        return OutboxPublisher.publish(
            aggregate_type='Location',
            aggregate_id=str(location.id),
            event_type='LocationCreated',
            payload={
                'id': str(location.id),
                'title': location.title,
                'description': location.description,
                'latitude': location.latitude,
                'longitude': location.longitude,
                'address': location.address,
                'is_public': location.is_public,
                'owner_id': str(location.owner_id),
                'created_at': location.created_at.isoformat() if location.created_at else None,
            }
        )
    
    @staticmethod
    def publish_location_updated(location) -> OutboxEvent:
        """Подія: локацію оновлено."""
        return OutboxPublisher.publish(
            aggregate_type='Location',
            aggregate_id=str(location.id),
            event_type='LocationUpdated',
            payload={
                'id': str(location.id),
                'title': location.title,
                'description': location.description,
                'latitude': location.latitude,
                'longitude': location.longitude,
                'address': location.address,
                'is_public': location.is_public,
                'updated_at': location.updated_at.isoformat() if location.updated_at else None,
            }
        )
    
    @staticmethod
    def publish_location_deleted(location_id: str, owner_id: str) -> OutboxEvent:
        """Подія: локацію видалено (soft delete)."""
        return OutboxPublisher.publish(
            aggregate_type='Location',
            aggregate_id=str(location_id),
            event_type='LocationDeleted',
            payload={
                'id': str(location_id),
                'owner_id': str(owner_id),
                'deleted_at': timezone.now().isoformat(),
            }
        )
