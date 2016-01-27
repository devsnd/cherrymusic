from django.contrib import admin
from .models import User, Playlist, Track, UserSettings, HotkeysSettings, MiscSettings


@admin.register(User, Playlist, Track, UserSettings, HotkeysSettings, MiscSettings)
class CoreAdmin(admin.ModelAdmin):
    pass
