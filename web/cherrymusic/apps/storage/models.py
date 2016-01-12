from pathlib import Path
import logging

from tinytag import TinyTag

from django.db import models
from django.utils import timezone

logger = logging.getLogger(__name__)


class Directory(models.Model):
    parent = models.ForeignKey('self', null=True)
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
        for f in self.file_set.all():
            logger.debug('Indexing %s' % f)
            if not f.exists():
                f.delete()
                deleted_files += 1
        # remove all stale directories:
        for d in Directory.objects.filter(parent=self):
            if not d.exists():
                d.delete()
                deleted_directories += 1
        # add all files and directories
        for sub_path in Path(self.absolute_path()).iterdir():
            if sub_path.is_file():
                # index all indexable files
                f = File(filename=sub_path.name, directory=self)
                if f.indexable():
                    try:
                        # check if the file was already indexed:
                        f = File.objects.get(filename=sub_path.name, directory=self)
                    except File.DoesNotExist:
                        f.index_unindexed_metadata()
                        f.save()
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

    def save(self, *args, is_basedir=False, **kwargs):
        if self.parent is None and not is_basedir:
            raise IndexError('Cannot index directory without a parent, unless it is the basedir!')
        super().save(*args, **kwargs)

    @classmethod
    def get_basedir(cls):
        if not hasattr(cls, '_cached_basedir'):
            cls._cached_basedir = Directory.objects.get(parent=None)
        return cls._cached_basedir


class File(models.Model):
    filename = models.CharField(max_length=255)
    directory = models.ForeignKey(Directory)

    meta_index_date = models.DateField(null=True, blank=True)

    meta_track = models.CharField(max_length=255, null=True, blank=True)
    meta_track_total = models.CharField(max_length=255, null=True, blank=True)
    meta_title = models.CharField(max_length=255, null=True, blank=True)
    meta_artist = models.CharField(max_length=255, null=True, blank=True)
    meta_album = models.CharField(max_length=255, null=True, blank=True)
    meta_year = models.CharField(max_length=255, null=True, blank=True)
    meta_genre = models.CharField(max_length=255, null=True, blank=True)
    meta_duration = models.FloatField(null=True, blank=True)

    @classmethod
    def index_unindexed_metadata(cls):
        for f in File.objects.filter(meta_index_date__isnull=True):
            f.parse_metadata()
            f.meta_index_date = timezone.now()
            f.save()

    def __str__(self):
        return self.filename

    def indexable(self):
        supported_file_types = ('.mp3', '.flac', '.ogg')
        return self.filename.lower().endswith(supported_file_types)

    def absolute_path(self):
        return self.directory.absolute_path() / self.filename

    def relative_path(self):
        return self.directory.relative_path() / self.filename

    def exists(self):
        return self.absolute_path().exists()

    def parse_metadata(self):
        # Errors with some mp3 files
        try:
            tag = TinyTag.get(str(self.absolute_path()))

            self.meta_track = tag.track.zfill(2) if tag.track else None
            self.meta_track_total = tag.track_total
            self.meta_title = tag.title
            self.meta_artist = tag.artist
            self.meta_album = tag.album
            self.meta_year = tag.year
            self.meta_genre = tag.genre
            self.meta_duration = tag.duration
        except:
            logger.info('Fail to get meta data from %s', str(self.absolute_path()))

