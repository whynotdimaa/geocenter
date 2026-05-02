import django_filters
from .models import Location


class LocationFilter(django_filters.FilterSet):
    """
    Фільтри для списку локацій.
    Приклад: /api/locations/?category=1&is_public=true&title=київ
    """
    title = django_filters.CharFilter(lookup_expr='icontains', label='Назва містить')
    category = django_filters.NumberFilter(field_name='category__id', label='ID категорії')
    is_public = django_filters.BooleanFilter(label='Публічна')
    owner = django_filters.NumberFilter(field_name='owner__id', label='ID власника')
    tag = django_filters.CharFilter(field_name='tags__name', lookup_expr='icontains', label='Тег')

    # Фільтр за датою
    created_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')

    class Meta:
        model = Location
        fields = ['title', 'category', 'is_public', 'owner', 'tag', 'created_after', 'created_before']