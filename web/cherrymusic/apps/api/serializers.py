from rest_framework import serializers

from cherrymusic.apps.storage.models import File, Directory
from cherrymusic.apps.core.models import Playlist, Track, User, UserSettings, HotkeysSettings, MiscSettings




class FileSerializer(serializers.ModelSerializer):
    path = serializers.SerializerMethodField('get_relative_path')

    class Meta:
        model = File
        fields = (
            'id',
            'filename',
            'path',
            'meta_track',
            'meta_track_total',
            'meta_title',
            'meta_artist',
            'meta_album',
            'meta_year',
            'meta_genre',
            'meta_duration',
            'meta_index_date',
        )

    @staticmethod
    def get_relative_path(file):
        return str(file.relative_path())

class DirectorySerializer(serializers.ModelSerializer):
    path = serializers.SerializerMethodField('get_sanitized_path')

    class Meta:
        model = Directory
        fields = ('parent', 'path', 'id')

    @staticmethod
    def get_sanitized_path(dir):
        # do not serialize the basedir path
        if dir.parent is None:
            return
        else:
            return dir.path

class TrackSerializer(serializers.ModelSerializer):
    data = serializers.SerializerMethodField('serialize_data')

    class Meta:
        model = Track
        fields = ('playlist', 'order', 'type', 'file', 'data' )

    @staticmethod
    def serialize_data(track):
        if track.type == Track.TYPE.LOCAL_STORAGE:
            serializer = FileSerializer()
            return serializer.to_representation(track.file)
        else:
            raise KeyError('Cannot serialize Track %s of type %s' % (track, track.type))

class PlaylistSerializer(serializers.ModelSerializer):
    tracks = serializers.SerializerMethodField()
    owner_name = serializers.SerializerMethodField()

    class Meta:
        model = Playlist
        fields = ('id', 'name', 'owner', 'public', 'tracks', 'owner_name', 'created_at')

    @staticmethod
    def get_owner_name(obj):
        return obj.owner.username

    @staticmethod
    def get_tracks(obj):
        serializer = TrackSerializer()
        return [serializer.to_representation(track) for track in obj.track_set.all().order_by('order')]

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'last_login', 'is_logged', 'is_superuser')

class CreateUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'is_superuser', 'email', 'password')

class HotkeysSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = HotkeysSettings
        fields = ('increase_volume', 'decrease_volume', 'toggle_mute', 'previous_track',
            'next_track', 'toggle_play')

class MiscSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = MiscSettings
        fields = ('auto_play', 'confirm_closing', 'show_album_art', 'remove_when_queue')

class UserSettingsSerializer(serializers.ModelSerializer):
    hotkeys = HotkeysSettingsSerializer()
    misc = MiscSettingsSerializer()
    class Meta:
        model = UserSettings
        fields = ('user', 'hotkeys', 'misc')

    def update(self, instance, validated_data):
        misc_data = validated_data.pop('misc')
        misc = instance.misc

        for key, value in misc_data.items():
            setattr(misc, key, value)
        misc.save()

        hotkeys_data = validated_data.pop('hotkeys')
        hotkeys = instance.hotkeys

        for key, value in hotkeys_data.items():
            setattr(hotkeys, key, value)

        hotkeys.save()

        return instance