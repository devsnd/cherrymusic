from django.contrib import admin
from .models import User, Playlist, Track


@admin.register(User, Playlist, Track)
class CoreAdmin(admin.ModelAdmin):
    pass
