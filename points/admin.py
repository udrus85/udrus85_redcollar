from django.contrib import admin
from .models import Point, Message

# Register your models here.

@admin.register(Point)
class PointAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'latitude', 'longitude']

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['user', 'point', 'content', 'created_at']
