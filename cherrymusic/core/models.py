from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from storage.models import File

from django.db.models import signals


class User(AbstractUser):
    pass

class HotkeysSettings(models.Model):
    increase_volume = models.CharField(max_length=50, default='ctrl+up')
    decrease_volume = models.CharField(max_length=50, default='ctrl+down')
    toggle_mute = models.CharField(max_length=50, default='ctrl+m')
    previous_track = models.CharField(max_length=50, default='ctrl+left')
    next_track = models.CharField(max_length=50, default='ctrl+right')
    toggle_play = models.CharField(max_length=50, default='space')

class MiscSettings(models.Model):
    auto_play = models.BooleanField(default=False)
    confirm_closing = models.BooleanField(default=True)
    show_album_art = models.BooleanField(default=True)
    remove_when_queue = models.BooleanField(default=True)

class UserSettings(models.Model):
    user = models.OneToOneField(User)
    hotkeys = models.OneToOneField(HotkeysSettings)
    misc = models.OneToOneField(MiscSettings)

def create_user_settings(sender, instance, created, **kwargs):
    """Create UserSettings for every new User."""
    if created:
        hotkeys = HotkeysSettings.objects.create()
        misc = MiscSettings.objects.create()
        UserSettings.objects.create(user=instance, hotkeys=hotkeys, misc=misc)

signals.post_save.connect(create_user_settings, sender=User, weak=False,
                          dispatch_uid='models.create_user_settings')


class Playlist(models.Model):
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(User)
    public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add = True)

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

