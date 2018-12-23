from django.contrib.auth import get_user_model
from django.db import models

from storage.models import File

User = get_user_model()


class Playlist(models.Model):
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(User, on_delete=models.PROTECT)
    public = models.BooleanField(default=True)


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

    file = models.ForeignKey(File, null=True, on_delete=models.PROTECT)  # local storage
    youtube_url = models.URLField(null=True)
