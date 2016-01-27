from django.contrib import admin
from django.contrib.admin import ModelAdmin
from .models import File, Directory


class DirectoryAdmin(ModelAdmin):
    list_display = [
        'parent',
        'path',
    ]

class FileAdmin(ModelAdmin):
    list_display = [
        'filename',
        'directory',
        'meta_index_date',
        'meta_track',
        'meta_track_total',
        'meta_title',
        'meta_artist',
        'meta_album',
        'meta_year',
        'meta_genre',
        'meta_duration',
    ]

admin.site.register(File, FileAdmin)
admin.site.register(Directory, DirectoryAdmin)