from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserProfile


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Профіль'


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('email', 'username', 'is_email_verified', 'is_staff', 'date_joined')
    list_filter = ('is_staff', 'is_active', 'is_email_verified')
    search_fields = ('email', 'username')
    ordering = ('-date_joined',)

    # Додаємо наші кастомні поля до форми редагування
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Додаткова інформація', {
            'fields': ('avatar', 'bio', 'is_email_verified')
        }),
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'language', 'coord_units', 'dark_mode')
    search_fields = ('user__email',)