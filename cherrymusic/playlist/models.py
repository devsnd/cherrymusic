from django.contrib.auth import get_user_model
from django.db import models

from storage.models import File, Youtube

User = get_user_model()




class Playlist(models.Model):
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(User, on_delete=models.PROTECT)
    public = models.BooleanField(default=True)

    def get_active_track_idx(self):
        position = PlaylistPosition.objects.filter(playlist=self, user=self.owner).first()
        if position:
            return position.active_track_idx
        return 0

    def get_playback_position(self):
        position = PlaylistPosition.objects.filter(playlist=self, user=self.owner).first()
        if position:
            return position.playback_position
        return 0.0


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
    class Meta:
        unique_together = (
            ('playlist', 'order'),
        )

    class TYPE:
        FILE = 0
        YOUTUBE_URL = 1

    TYPE_CHOICES = (
        (TYPE.FILE, 'FILE'),
        (TYPE.YOUTUBE_URL, 'YOUTUBE_URL'),
    )

    def __str__(self):
        if self.type == Track.TYPE.FILE:
            return f'{self.order} FILE {self.file.filename}'
        elif self.type == Track.TYPE.YOUTUBE_URL:
            return f'{self.order} YOUTUBE {self.youtube.title}'
        else:
            return f'{self.order} TYPE {self.type}'

    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE, related_name='tracks')
    order = models.PositiveSmallIntegerField()
    type = models.PositiveSmallIntegerField(choices=TYPE_CHOICES, default=TYPE.FILE)

    file = models.ForeignKey(File, null=True, blank=True, on_delete=models.CASCADE)
    youtube = models.ForeignKey(Youtube, null=True, blank=True, on_delete=models.CASCADE)
