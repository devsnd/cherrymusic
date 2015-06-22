from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from storage.models import File


class User(AbstractUser):
    pass


class Playlist(models.Model):
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(User)
    public = models.BooleanField(default=True)


class Track(models.Model):
    class TYPE:
        LOCAL_STORAGE = 0
        STREAM_URL = 1

    TYPE_CHOICES = (
        (TYPE.LOCAL_STORAGE, 'LOCAL_STORAGE'),
        (TYPE.STREAM_URL, 'STREAM_URL'),
    )

    playlist = models.ForeignKey(Playlist)
    order = models.IntegerField()
    type = models.IntegerField(choices=TYPE_CHOICES, default=TYPE.LOCAL_STORAGE)

    file = models.ForeignKey(File, null=True) # local storage

