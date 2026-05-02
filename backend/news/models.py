from django.contrib.gis.db import models


class NewsPoint(models.Model):
    title = models.CharField(max_length=200, verbose_name="Заголовок новини")
    content = models.TextField(verbose_name="Зміст")

    # Гео-координати для новини
    location = models.PointField(srid=4326, verbose_name="Місце події")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Новина з геолокацією"
        verbose_name_plural = "Новини з геолокацією"