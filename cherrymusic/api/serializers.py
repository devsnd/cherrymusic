import os

from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers
from rest_framework.reverse import reverse

from storage.models import File, Directory, MetaData, Artist, Album, Genre, Youtube
from playlist.models import Playlist, Track, PlaylistPosition

User = get_user_model()


class ArtistSerializer(serializers.ModelSerializer):
    album_thumbnail_gif_b64 = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Artist
        fields = (
            'id',
            'name',
            'album_thumbnail_gif_b64',
        )

    def get_album_thumbnail_gif_b64(self, instance):
        return (
            album.thumbnail_gif_b64
            for album in
            Album.objects
            .filter(albumartist=instance)
            .only('thumbnail_gif')
        )


class AlbumSerializer(serializers.ModelSerializer):
    albumartist = ArtistSerializer(read_only=True)

    class Meta:
        model = Album
        fields = (
            'name',
            'albumartist',
            'thumbnail_gif_b64',
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
    stream_url = serializers.SerializerMethodField()
    meta_data = MetaDataSerializer(read_only=True)

    class Meta:
        model = File
        fields = (
            'id',
            'filename',
            'meta_data',
            'stream_url',

        )

    def get_stream_url(self, obj):
        return reverse('file-stream', args=[obj.id])


class YoutubeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Youtube
        fields = (
            'id',
            'youtube_id',
            'title',
            'views',
            'duration',
        )


class SimpleDirectorySerializer(serializers.ModelSerializer):
    path = serializers.SerializerMethodField('get_sanitized_path')
    parent = serializers.SerializerMethodField()

    class Meta:
        model = Directory
        fields = [
            'id',
            'parent',
            'path',
        ]

    def get_parent(self, instance):
        if instance.parent is None:
            return -1
        return instance.parent.id

    @staticmethod
    def get_sanitized_path(dir):
        # do not serialize the basedir path
        if dir.parent is None:
            path = dir.path[:-1] if dir.path.endswith(os.path.sep) else dir.path
            return path.rsplit(os.path.sep, 1)[-1]
        else:
            return dir.path

class DirectorySerializer(SimpleDirectorySerializer):
    sub_directories = serializers.SerializerMethodField()
    files = serializers.SerializerMethodField()

    class Meta:
        model = Directory
        fields = SimpleDirectorySerializer.Meta.fields + [
            'sub_directories',
            'files',
        ]

    def get_sub_directories(self, obj):
        return [
            SimpleDirectorySerializer().to_representation(dir)
            for dir in obj.subdirectories.order_by('path').all()
        ]

    def get_files(self, obj):
        return [
            FileSerializer().to_representation(file)
            for file in obj.files.order_by('filename')
        ]


class TrackSerializer(serializers.ModelSerializer):
    file = FileSerializer(allow_null=True)
    youtube = YoutubeSerializer(allow_null=True)
    playlist = serializers.PrimaryKeyRelatedField(allow_null=True, read_only=True)

    class Meta:
        model = Track
        fields = (
            'playlist',
            'order',
            'type',
            'file',
            'youtube',
        )

class PlaylistSerializer(serializers.ModelSerializer):
    tracks = TrackSerializer(many=True)
    owner_name = serializers.SerializerMethodField(read_only=True)
    active_track_idx = serializers.IntegerField(source='get_active_track_idx')
    playback_position = serializers.IntegerField(source='get_playback_position')

    class Meta:
        model = Playlist
        fields = [
            'id',
            'name',
            'owner',
            'owner_name',
            'tracks',
            'active_track_idx',
            'playback_position',
       ]

    def get_active_track_idx(self, instance):
        position = PlaylistPosition.objects.filter(
            playlist=instance,
            user=self.request.user,
        ).first()
        if position:
            return position.active_track_id
        return 0

    def get_playback_position(self, instance):
        position = PlaylistPosition.objects.filter(
            playlist=instance,
            user=self.request.user,
        ).first()
        if position:
            return position.playback_position
        return 0.0

    @staticmethod
    def get_owner_name(obj):
        return obj.owner.username

    def create(self, validated_data):
        print(validated_data)
        active_track_idx = validated_data.pop('active_track_idx')
        playlist_position = validated_data.pop('playlist_position')
        tracks_data = validated_data.pop('tracks')
        validated_data.pop('id')  # new playlist have id = -1, which is invalid

        with transaction.atomic():
            playlist = Playlist.objects.create(**validated_data)
            # sync playback position
            PlaylistPosition.objects.update_or_create(
                user=self.request.user,
                playlist=playlist,
                defaults=dict(
                    playlist_position=playlist_position,
                    active_track_idx=active_track_idx,
                )
            )
            # sync tracks
            for idx, track_data in enumerate(tracks_data):
                # make sure the order is not corrupted when saving to db
                track_data['order'] = idx
                track_data.pop('id', '')  # this will be set by the database
                track_data.pop('playlist', '')  # references playlist id = -1
                print(track_data)

                youtube = None
                youtube_data = track_data.pop('youtube')
                if youtube_data:
                    youtube_id = youtube_data.pop('youtube_id')
                    youtube = Youtube.objects.get_or_create(
                        video_id=youtube_id,
                        defaults=youtube_data
                    )[0]
                file = None
                file_data = track_data.pop('file')
                if file_data:
                    file = File.objects.get(file_data['id'])

                Track.objects.create(
                    playlist=playlist,
                    file=file,
                    youtube=youtube,
                    **track_data
                )
        return playlist


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username',)
