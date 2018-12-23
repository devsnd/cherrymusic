from django.contrib import admin

from utils.autoadmin import generate_and_register_admin, ObjectActionAdminMixin
from .models import File, Directory, MetaData, Album, Artist, Genre

@admin.register(File)
class FileAdmin(ObjectActionAdminMixin, admin.ModelAdmin):
    search_fields = [
        'meta_data__artist__norm_name',
        'meta_data__artist__name',
        'meta_data__album__name',
        'meta_data__title',
    ]

    list_display = [
        'id',
        'filename',
        'directory',
        'meta_indexed_at',
        'meta_data',
    ]

    object_actions = [
        'update_metadata'
    ]

@admin.register(Directory)
class DirectoryAdmin(ObjectActionAdminMixin, admin.ModelAdmin):
    list_display = [
        'id',
        'parent',
        'path',
    ]

    object_actions = [
        'reindex'
    ]

generate_and_register_admin(MetaData)
generate_and_register_admin(Album)
generate_and_register_admin(Artist)
generate_and_register_admin(Genre)
