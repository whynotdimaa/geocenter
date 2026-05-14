from django.contrib.gis import admin
from .models import Location, Category, Tag
from .outbox import OutboxEvent


@admin.register(Location)
class LocationAdmin(admin.GISModelAdmin):
    """Адмінка з вбудованою картою для редагування точок."""
    list_display = ('title', 'owner', 'category', 'is_public', 'created_at')
    list_filter = ('is_public', 'category', 'created_at')
    search_fields = ('title', 'description', 'address', 'owner__email')
    filter_horizontal = ('tags',)
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'color')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(OutboxEvent)
class OutboxEventAdmin(admin.ModelAdmin):
    """Адмінка для моніторингу outbox подій."""
    list_display = ('event_type', 'aggregate_type', 'aggregate_id', 'status', 'created_at', 'processed_at')
    list_filter = ('status', 'event_type', 'aggregate_type', 'created_at')
    search_fields = ('aggregate_id', 'event_type', 'payload')
    readonly_fields = ('id', 'created_at')
    ordering = ('-created_at',)
    
    def has_add_permission(self, request):
        """Забороняємо ручне створення подій."""
        return False