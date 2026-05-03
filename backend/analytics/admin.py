from django.contrib import admin
from .models import LocationView, ClusterResult


@admin.register(LocationView)
class LocationViewAdmin(admin.ModelAdmin):
    list_display = ('location', 'user', 'ip_address', 'viewed_at')
    list_filter = ('viewed_at',)
    search_fields = ('location__title', 'user__email', 'ip_address')
    readonly_fields = ('location', 'user', 'ip_address', 'viewed_at')
    ordering = ('-viewed_at',)

    def has_add_permission(self, request):
        return False  # логи тільки читаємо, не створюємо вручну


@admin.register(ClusterResult)
class ClusterResultAdmin(admin.ModelAdmin):
    list_display = ('user', 'n_clusters', 'created_at')
    list_filter = ('n_clusters', 'created_at')
    search_fields = ('user__email',)
    readonly_fields = ('user', 'n_clusters', 'result_json', 'created_at')
    ordering = ('-created_at',)

    def has_add_permission(self, request):
        return False