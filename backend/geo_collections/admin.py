from django.contrib import admin
from .models import Collection, CollectionMember


class CollectionMemberInline(admin.TabularInline):
    model = CollectionMember
    extra = 0
    fields = ('user', 'role', 'joined_at')
    readonly_fields = ('joined_at',)


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'is_public', 'locations_count', 'members_count', 'created_at')
    list_filter = ('is_public', 'created_at')
    search_fields = ('name', 'description', 'owner__email')
    readonly_fields = ('invite_token', 'created_at', 'updated_at')
    filter_horizontal = ('locations',)
    inlines = (CollectionMemberInline,)
    ordering = ('-created_at',)


@admin.register(CollectionMember)
class CollectionMemberAdmin(admin.ModelAdmin):
    list_display = ('user', 'collection', 'role', 'joined_at')
    list_filter = ('role',)
    search_fields = ('user__email', 'collection__name')
