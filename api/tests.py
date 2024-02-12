import os
from django.test import TestCase
from django.conf import settings
from django.urls import reverse

from songs.factories import SongFactory

class DownloadTests(TestCase):
    def test_download(self):
        # Arrange
        song = SongFactory(filename='test.mod', folder='T')
        remote_file_content = b'Test file content'
        main_archive_dir = settings.MAIN_ARCHIVE_DIR
        target_directory = os.path.join(main_archive_dir, song.folder)

        if not os.path.exists(target_directory):
            os.mkdir(target_directory)

        remote_file_path = os.path.join(target_directory, f'{song.filename}.zip')

        with open(remote_file_path, 'wb') as remote_file:
            remote_file.write(remote_file_content)

        # Act
        response = self.client.get(reverse('song_download', kwargs={'pk': song.pk}))

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, remote_file_content)
