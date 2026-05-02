from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    # CustomUser: розширений User
    email = models.EmailField(_("email address"), unique=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    is_email_verified = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email


class UserProfile(models.Model):
    # UserProfile: налаштування
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    language = models.CharField(max_length=10, default='uk')
    coord_units = models.CharField(
        max_length=20,
        choices=[('decimal', 'Decimal Degrees'), ('dms', 'Degrees Minutes Seconds')],
        default='decimal'
    )
    dark_mode = models.BooleanField(default=False)

    def __str__(self):
        return f"Profile for {self.user.email}"
