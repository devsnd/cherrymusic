from django.contrib.auth import get_user_model
from rest_framework import serializers
from storage.models import File, Directory, MetaData, Artist, Album, Genre
from playlist.models import Playlist, Track


User = get_user_model()

class AlbumSerializer(serializers.ModelSerializer):
    class Meta:
        model = Album
        fields = (
            'name',
        )


class ArtistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Artist
        fields = (
            'id',
            'name',
        )


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = (
            'id',
            'name',
        )


class MetaDataSerializer(serializers.ModelSerializer):
    artist = ArtistSerializer(read_only=True)
    genre = GenreSerializer(read_only=True)
    album = AlbumSerializer(read_only=True)

    class Meta:
        model = MetaData
        fields = (
            'track',
            'track_total',
            'title',
            'artist',
            'album',
            'year',
            'genre',
            'duration',
        )


class FileSerializer(serializers.ModelSerializer):
    path = serializers.SerializerMethodField('get_relative_path')
    meta_data = MetaDataSerializer(read_only=True)

    class Meta:
        model = File
        fields = (
            'id',
            'filename',
            'path',
            'meta_data',
        )

    @staticmethod
    def get_relative_path(file):
        return str(file.relative_path())


class SimpleDirectorySerializer(serializers.ModelSerializer):
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

class DirectorySerializer(serializers.ModelSerializer):
    path = serializers.SerializerMethodField('get_sanitized_path')
    sub_directories = serializers.SerializerMethodField()
    files = serializers.SerializerMethodField()

    class Meta:
        model = Directory
        fields = (
            'parent',
            'path',
            'id',
            'sub_directories',
            'files',
        )

    def get_sub_directories(self, obj):
        return [
            SimpleDirectorySerializer().to_representation(dir)
            for dir in obj.subdirectories
        ]

    def get_files(self, obj):
        return [
            FileSerializer().to_representation(file)
            for file in obj.files
        ]

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
