from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, UserProfile


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Створює UserProfile тільки при першій реєстрації."""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Зберігає профіль при збереженні користувача (якщо профіль вже існує)."""
    # get_or_create захищає від помилки якщо профіль чомусь не існує
    profile, _ = UserProfile.objects.get_or_create(user=instance)
    profile.save()