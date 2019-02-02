from django.contrib import admin
from django.utils.html import escape
from django.utils.safestring import mark_safe

from playlist.models import Playlist, Track
from utils.autoadmin import generate_and_register_admin

generate_and_register_admin(Track)

@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'name',
        'owner',
        'public',
        '_tracks',
        'get_active_track_idx',
        'get_playback_position',
    ]

    @mark_safe
    def _tracks(self, obj):
        return '<br>'.join(escape(str(t)) for t in obj.tracks.all())
