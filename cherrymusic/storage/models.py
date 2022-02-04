import base64
import os

from PIL import Image
from django.conf import settings
from django.db import models
from io import BytesIO
from pathlib import Path
import logging
from django.utils import timezone

from ext.tinytag import TinyTag, TinyTagException
from utils.models import BaseModel
from utils.natural_language import normalize_name

logger = logging.getLogger(__name__)


class Directory(BaseModel):
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='subdirectories')
    path = models.CharField(max_length=255)

    def __str__(self):
        return self.path

    def absolute_path(self):
        if not hasattr(self, '_cached_absolute_path'):
            if self.parent is None: # only the basedir has no parent
                self._cached_absolute_path = Path(self.path)
            else:
                self._cached_absolute_path = self.parent.absolute_path() / self.path
        return self._cached_absolute_path

    def relative_path(self):
        if self.parent is None:
            return Path()
        else:
            return self.parent.relative_path() / self.path

    def get_sub_path_directories(self, path_elements):
        current, *rest = path_elements
        # check if the directory exists in database on the fly
        try:
            dir = Directory.objects.get(parent=self, path=current)
        except Directory.DoesNotExist:
            # try to index the directory if it does not exist yet
            dir = Directory(parent=self, path=current)
            if dir.exists():
                dir.save()
            else:
                raise FileNotFoundError('The directory %s does not exist!' % dir.absolute_path())
        if rest:
            return [dir] + dir.get_sub_path_directories(rest)
        else:
            return [dir]

    def listdir(self):
        return (
            File.objects.filter(directory=self).order_by('filename').all(),
            Directory.objects.filter(parent=self).order_by('path').all(),
        )

    def exists(self):
        return self.absolute_path().exists()

    def reindex(self, recursively=True):
        deleted_files = 0
        deleted_directories = 0
        indexed_files = 0
        indexed_directories = 0
        # remove all stale files
        for f in self.files.all():
            if not f.exists():
                f.delete()
                deleted_files += 1
        # remove all stale directories:
        for d in Directory.objects.filter(parent=self):
            if not d.exists():
                d.delete()
                deleted_directories += 1
        # add all files and directories
        parent_path = self.absolute_path()
        if parent_path.exists():
            for sub_path in Path(parent_path).iterdir():
                if sub_path.is_file() and File.indexable(sub_path.name):
                    abs_path = parent_path / sub_path
                    # index all indexable files
                    created, file = File.objects.get_or_create(
                        filename=sub_path.name,
                        directory=self,
                        defaults=dict(
                            size=os.stat(abs_path.absolute()).st_size,
                        )
                    )
                    if created:
                        indexed_files += 1
                elif sub_path.is_dir():
                    if sub_path.name == '.':
                        continue
                    sub_dir, created = Directory.objects.get_or_create(parent=self, path=sub_path.name)
                    if created:
                        indexed_directories += 1

                    if recursively:
                        # index everything recursively, keep track of total files indexed
                        del_files, del_directories, idx_files, idx_directories = sub_dir.reindex()
                        deleted_files += del_files
                        deleted_directories += del_directories
                        indexed_files += idx_files
                        indexed_directories += idx_directories
                else:
                    logger.info('Unknown filetype %s', sub_path)
        return (
            deleted_files,
            deleted_directories,
            indexed_files,
            indexed_directories,
        )


class Artist(BaseModel):
    name = models.CharField(max_length=255)
    norm_name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        self.norm_name = normalize_name(self.name)
        super().save(force_insert=False, force_update=False, using=None,
             update_fields=None)

    @classmethod
    def get_for_name(cls, name):
        if not name:
            return
        norm_name = normalize_name(name)
        if not norm_name:
            return
        artist, created = cls.objects.get_or_create(
            norm_name=norm_name,
            defaults=dict(
                name=name,
            )
        )
        return artist


class Album(BaseModel):
    name = models.CharField(max_length=255)
    albumartist = models.ForeignKey(
        Artist,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='albums'
    )
    thumbnail_gif = models.BinaryField(max_length=20 * 1024, null=True, blank=True)

    thumbnail_size = (32, 32)

    @property
    def thumbnail_gif_b64(self):
        if self.thumbnail_gif:
            b64_string = base64.b64encode(self.thumbnail_gif).decode('ascii')
            return f'data:image/gif;base64,{b64_string}'

    @classmethod
    def img_data_to_thumbnail(cls, img):
        im = Image.open(img)
        im.thumbnail(cls.thumbnail_size)
        out_stream = BytesIO()
        im = im.convert('P', palette=Image.ADAPTIVE, colors=32)
        im.save(out_stream, "GIF")
        out_stream.seek(0)
        return out_stream.read()

    def get_image_from_tracks(self):
        for file in File.objects.filter(meta_data__album=self):
            image_data = file.get_meta_data_image()
            if image_data is not None:
                self.thumbnail_gif = Album.img_data_to_thumbnail(BytesIO(image_data))
                self.save()
                return
        for file in File.objects.filter(meta_data__album=self):
            dir_path = os.path.dirname(file.absolute_path())
            for file in os.listdir(dir_path):
                if file.lower().endswith(('.jpg', '.gif', '.jpeg')):
                    abs_path = os.path.join(dir_path, file)
                    self.thumbnail_gif = Album.img_data_to_thumbnail(abs_path)
                    self.save()
                    return


    @classmethod
    def get_for_name(cls, album, albumartist):
        return cls.objects.get_or_create(name=album, albumartist=albumartist)[0]


class Genre(BaseModel):
    name = models.CharField(max_length=255)

    def save(self, *args, **kwargs):
        self.name = normalize_name(self.name)
        super().save(*args, **kwargs)

    @classmethod
    def get_for_name(cls, genre):
        return Genre.objects.get_or_create(name=normalize_name(genre))[0]


class MetaData(BaseModel):
    track = models.IntegerField(null=True, blank=True)
    track_total = models.IntegerField(null=True, blank=True)
    title = models.CharField(max_length=255, null=True, blank=True)
    artist = models.ForeignKey(Artist, null=True, blank=True, on_delete=models.SET_NULL, related_name='tracks')
    album = models.ForeignKey(Album, null=True, blank=True, on_delete=models.SET_NULL, related_name='tracks')
    year = models.IntegerField(null=True, blank=True)
    genre = models.ForeignKey(Genre, null=True, blank=True, on_delete=models.SET_NULL)
    duration = models.FloatField(null=True, blank=True)

    file = models.OneToOneField('storage.File', on_delete=models.CASCADE, related_name='meta_data')

    def __str__(self):
        return f'{self.track} {self.artist} - {self.title}'

    @classmethod
    def create_for_file(cls, file):
        try:
            tag = TinyTag.get(str(file.absolute_path()))
        except TinyTagException:
            return
        artist = Artist.get_for_name(tag.artist)
        albumartist = Artist.get_for_name(tag.albumartist)
        album = Album.get_for_name(tag.album, albumartist or artist) if tag.album else None
        genre = Genre.get_for_name(tag.genre) if tag.genre else None
        meta_data = MetaData.objects.create(
            track=int(tag.track) if tag.track else None,
            track_total=int(tag.track_total) if tag.track_total else None,
            title=tag.title,
            artist=artist,
            album=album,
            year=int(tag.year) if tag.year else None,
            genre=genre,
            duration=tag.duration,
            file=file,
        )
        return meta_data


class Youtube(BaseModel):
    youtube_id = models.CharField(max_length=255, unique=True)
    thumbnail_url = models.URLField()
    title = models.CharField(max_length=255)
    views = models.PositiveIntegerField()
    duration = models.PositiveIntegerField()


class File(BaseModel):
    filename = models.CharField(max_length=255)
    directory = models.ForeignKey(Directory, on_delete=models.CASCADE, related_name='files')
    size = models.PositiveIntegerField()

    meta_indexed_at = models.DateField(null=True, blank=True)

    def get_meta_data_image(self):
        tinytag = TinyTag.get(str(self.absolute_path()), image=True)
        return tinytag.get_image()

    def update_metadata(self):
        MetaData.create_for_file(self)
        self.meta_indexed_at = timezone.now()
        self.save()

    @classmethod
    def index_unindexed_metadata(cls):
        for f in File.objects.filter(meta_indexed_at__isnull=True):
            f.update_metadata()

    def __str__(self):
        return self.filename

    @classmethod
    def indexable(self, path):
        supported_file_types = tuple(settings.SUPPORTED_FILETYPES)
        return path.lower().endswith(supported_file_types)

    def absolute_path(self):
        return self.directory.absolute_path() / self.filename

    def relative_path(self):
        return self.directory.relative_path() / self.filename

    def exists(self):
        return self.absolute_path().exists()
