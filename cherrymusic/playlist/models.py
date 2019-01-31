from django.contrib.auth import get_user_model
from django.db import models

from storage.models import File, Youtube

User = get_user_model()




class Playlist(models.Model):
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(User, on_delete=models.PROTECT)
    public = models.BooleanField(default=True)


class PlaylistPosition(models.Model):
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    active_track_idx = models.SmallIntegerField()
    playback_position = models.FloatField()


    class Meta:
        unique_together = [
            ('playlist', 'user')
        ]


class Track(models.Model):
    class TYPE:
        FILE = 0
        YOUTUBE_URL = 1

    TYPE_CHOICES = (
        (TYPE.FILE, 'FILE'),
        (TYPE.YOUTUBE_URL, 'YOUTUBE_URL'),
    )

    playlist = models.ForeignKey(Playlist, on_delete=models.PROTECT)
    order = models.PositiveSmallIntegerField(unique=True)
    type = models.PositiveSmallIntegerField(choices=TYPE_CHOICES, default=TYPE.FILE)

    file = models.ForeignKey(File, null=True, blank=True, on_delete=models.CASCADE)
    youtube = models.ForeignKey(Youtube, null=True, blank=True, on_delete=models.CASCADE)
