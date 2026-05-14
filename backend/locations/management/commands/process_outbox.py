"""
Outbox Relay — процесор подій з таблиці Outbox.

Читає невідправлені події та відправляє їх іншим мікросервісам.
В реальному середовищі це може бути Celery beat, cron, або окремий worker.

Використання:
    python manage.py process_outbox --limit 100

Або в crontab:
    * * * * * cd /app && python manage.py process_outbox >> /var/log/outbox.log 2>&1
"""
import json
import time
from datetime import datetime
from typing import List

import requests
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.conf import settings

from locations.outbox import OutboxEvent


class Command(BaseCommand):
    help = 'Process pending outbox events and deliver them to other services'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=100,
            help='Maximum number of events to process (default: 100)'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=10,
            help='Process events in batches of this size (default: 10)'
        )

    def handle(self, *args, **options):
        limit = options['limit']
        batch_size = options['batch_size']

        self.stdout.write(
            self.style.NOTICE(f'Starting outbox processing (limit: {limit}, batch: {batch_size})...')
        )

        processed = 0
        failed = 0

        # Обробляємо події по одній з блокуванням
        for _ in range(limit):
            try:
                with transaction.atomic():
                    # Блокуємо одну подію для обробки
                    event = OutboxEvent.objects.filter(
                        status=OutboxEvent.Status.PENDING
                    ).select_for_update(skip_locked=True).first()

                    if not event:
                        break  # Більше немає pending подій

                    success = self._process_event(event)
                    if success:
                        processed += 1
                        self.stdout.write(
                            self.style.SUCCESS(f'  ✓ {event.event_type} [{event.aggregate_id}]')
                        )
                    else:
                        failed += 1
            except Exception as e:
                failed += 1
                self.stderr.write(
                    self.style.ERROR(f'  ✗ Error processing event: {str(e)}')
                )

        total = processed + failed
        if total == 0:
            self.stdout.write(self.style.SUCCESS('No pending events found.'))
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nCompleted: {processed} processed, {failed} failed, {total} total'
                )
            )

    def _process_event(self, event: OutboxEvent) -> bool:
        """
        Відправляє подію іншим мікросервісам.
        
        В реальному проекті тут може бути:
        - HTTP webhook до інших сервісів
        - Публікація в Kafka/RabbitMQ
        - gRPC стрімінг
        
        Для демонстрації — HTTP POST до analytics_service або logging.
        """
        try:
            # Симуляція відправки — логуємо та позначаємо як оброблено
            # В реальності тут буде виклик до брокера повідомлень
            
            event_data = {
                'event_id': str(event.id),
                'event_type': event.event_type,
                'aggregate_type': event.aggregate_type,
                'aggregate_id': event.aggregate_id,
                'payload': event.payload,
                'created_at': event.created_at.isoformat(),
            }
            
            # Логуємо для демонстрації
            self.stdout.write(
                self.style.NOTICE(f'    Delivering: {json.dumps(event_data, ensure_ascii=False)}')
            )
            
            # TODO: Тут реальна відправка до брокера або HTTP webhook
            # Приклад HTTP webhook до analytics_service:
            # response = requests.post(
            #     f"{settings.ANALYTICS_SERVICE_URL}/api/events/",
            #     json=event_data,
            #     timeout=5
            # )
            # response.raise_for_status()
            
            # Симуляція успішної відправки
            time.sleep(0.01)  # Імітація мережевої затримки
            
            # Оновлюємо статус
            event.status = OutboxEvent.Status.PROCESSED
            event.processed_at = datetime.now()
            event.save(update_fields=['status', 'processed_at'])
            
            return True
            
        except Exception as e:
            # Збільшуємо лічильник спроб
            event.retry_count += 1
            
            # Якщо перевищено ліміт ретрайів — позначаємо як failed
            if event.retry_count >= 3:
                event.status = OutboxEvent.Status.FAILED
                event.error_message = str(e)
            
            event.save(update_fields=['retry_count', 'status', 'error_message'])
            
            return False
