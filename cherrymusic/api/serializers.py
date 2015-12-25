from django.contrib.auth import get_user_model
from rest_framework import serializers
from storage.models import File, Directory
from core.models import Playlist, Track, UserSettings, HotkeysSettings, MiscSettings


User = get_user_model()


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

class PlayListSerializer(serializers.ModelSerializer):
    tracks = serializers.SerializerMethodField()
    owner_name = serializers.SerializerMethodField()

    class Meta:
        model = Playlist
        fields = ('id', 'name', 'owner', 'public', 'tracks')

    @staticmethod
    def get_owner_name(obj):
        return obj.owner.username

    @staticmethod
    def get_tracks(obj):
        serializer = TrackSerializer()
        return [serializer.to_representation(track) for track in obj.track_set.all().order_by('order')]

class PlaylistDetailSerializer(PlayListSerializer):
    tracks = serializers.SerializerMethodField()
    owner_name = serializers.SerializerMethodField()

    class Meta:
        model = Playlist
        fields = ('id', 'name', 'owner', 'public', 'tracks', 'owner_name')


class PlaylistListSerializer(PlayListSerializer):
    class Meta:
        model = Playlist
        fields = ('id', 'name', 'owner', 'public')

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'is_superuser')

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
        # TODO: loops... and if not exist validated_data.get('auto_play', misc.auto_play)
        misc_data = validated_data.pop('misc')
        misc = instance.misc
        
        misc.auto_play = misc_data['auto_play'] 
        misc.confirm_closing = misc_data['confirm_closing']
        misc.show_album_art = misc_data['show_album_art']
        misc.remove_when_queue = misc_data['remove_when_queue']
        misc.save()

        hotkeys_data = validated_data.pop('hotkeys')
        hotkeys = instance.hotkeys

        hotkeys.increase_volume = hotkeys_data['increase_volume']
        hotkeys.decrease_volume = hotkeys_data['decrease_volume']
        hotkeys.toggle_mute = hotkeys_data['toggle_mute']
        hotkeys.previous_track = hotkeys_data['previous_track']
        hotkeys.next_track = hotkeys_data['next_track']
        hotkeys.toggle_play = hotkeys_data['toggle_play']

        hotkeys.save()

        return instance