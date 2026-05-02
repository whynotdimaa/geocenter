from rest_framework import viewsets
from .models import NewsPoint
from .serializers import NewsPointSerializer

class NewsPointViewSet(viewsets.ModelViewSet):
    queryset = NewsPoint.objects.all().order_by('-created_at')
    serializer_class = NewsPointSerializer