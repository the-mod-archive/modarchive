import os
from django.test import TestCase
from django.conf import settings
from django.urls import reverse

from songs.factories import SongFactory

class DownloadTests(TestCase):
    def setUp(self):
        self.song = SongFactory(filename='test.s3m', folder='T', format='s3m')
        self.remote_file_content = b'Test file content'
        self.main_archive_dir = settings.MAIN_ARCHIVE_DIR
        self.target_directory = os.path.join(self.main_archive_dir, self.song.format, self.song.folder)
        self.remote_file_path = os.path.join(self.target_directory, f'{self.song.filename}.zip')

        os.makedirs(self.target_directory, exist_ok=True)

        with open(self.remote_file_path, 'wb') as remote_file:
            remote_file.write(self.remote_file_content)

    def tearDown(self):
        if os.path.isfile(self.remote_file_path):
            os.remove(self.remote_file_path)

        try:
            os.rmdir(self.target_directory)
            os.rmdir(os.path.join(self.main_archive_dir, self.song.format))
        except OSError:
            pass

    def test_download(self):
        # Act
        response = self.client.get(reverse('song_download', kwargs={'pk': self.song.pk}))

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, self.remote_file_content)