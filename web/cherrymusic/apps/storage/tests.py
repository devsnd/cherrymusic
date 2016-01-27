import os
from pathlib import Path

from django.test import TestCase
from testfixtures import TempDirectory

from cherrymusic.apps.storage.models import Directory


class TestDirectoryModel(TestCase):
    def setUp(self):
        self.temp_dir = TempDirectory()
        self.base_path = self.temp_dir.makedir(('base'))
        self.base_dir = Directory(path=self.base_path)
        self.base_dir.save(is_basedir=True)

        self.test_dir = Directory(parent=self.base_dir, path='test')
        self.test_dir.save()

    def test_base_dir_absolute_path(self):
        self.assertEqual(Path(self.base_path), self.base_dir.absolute_path())
        
    def test_base_dir_relative_path(self):
        self.assertEqual(Path('.'), self.base_dir.relative_path())

    def test_absolute_path(self):
        test_path = self.temp_dir.makedir(os.path.join(self.base_path, 'test'))

        self.assertEqual(Path(test_path), self.test_dir.absolute_path())

    def test_relative_path(self):
        self.assertEqual(Path('test'), self.test_dir.relative_path())
    
    def test_get_sub_path_directories(self):
        paths_elements = ['test']
        self.assertEqual([self.test_dir], self.base_dir.get_sub_path_directories(paths_elements))

    def listdir(self):
        self.assertEqual(([], [self.test_dir]), self.base_dir.listdir())

    def test_exists(self):
        self.assertTrue(self.base_dir.exists())

    def test_get_basedir(self):
        delattr(Directory, '_cached_basedir')
        self.assertEqual(self.base_dir, Directory.get_basedir())

        