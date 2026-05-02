from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'
    verbose_name = 'Користувачі'

    def ready(self):
        # Підключає сигнали при старті застосунку.
        # БЕЗ ЦЬОГО signals.py не буде виконуватись!
        import users.signals  # noqa: F401