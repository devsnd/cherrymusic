from django.contrib.auth import get_user_model
from rest_framework import serializers
from storage.models import File, Directory
from core.models import Playlist, Track


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
        fields = ('type', 'data', 'playlist')

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
        fields = ('username',)