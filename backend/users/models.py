from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    # Можна додати додаткові поля, наприклад, аватар або роль
    bio = models.TextField(max_length=500, blank=True)

    def __str__(self):
        return self.username
