from django.db import models
from django.contrib.gis.db import models as gis_models
from django.contrib.gis.geos import Point as GEOSPoint
from django.contrib.auth.models import User

# Create your models here.

class Point(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='points')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    location = gis_models.PointField(geography=True, srid=4326)

    def save(self, *args, **kwargs):
        """
        Автоматическая синхронизация location с latitude/longitude.
        
        Важно: не работает с bulk_create() и QuerySet.update().
        Для bulk операций используйте explicit заполнение location.
        """
        # Всегда синхронизируем location с lat/lon
        if self.latitude is not None and self.longitude is not None:
            self.location = GEOSPoint(self.longitude, self.latitude, srid=4326)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Message(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='messages')
    point = models.ForeignKey(Point, on_delete=models.CASCADE, related_name='messages')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message by {self.user} on {self.point}"
