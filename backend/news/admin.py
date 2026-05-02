from django.contrib.gis import admin
from .models import NewsPoint

@admin.register(NewsPoint)
class NewsPointAdmin(admin.GISModelAdmin):
    list_display = ('title', 'created_at')
    search_fields = ('title',)
