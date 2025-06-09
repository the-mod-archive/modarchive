import os
import tempfile
import zipfile

from unittest.mock import patch
from django.conf import settings

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls.base import reverse

from homepage.tests import factories
from songs.models import Song
from uploads.models import NewSong

from songs import factories as song_factories
from uploads import factories as upload_factories
from uploads import constants

OCTET_STREAM = 'application/octet-stream'
SONG_TITLE = 'Test Song'
S3M_TITLE = 'Test S3M'
IT_TITLE = 'Test IT'
NOT_A_MOD_FILENAME = 'not_a_mod.txt'
TEST_MOD_FILENAME = 'test1.mod'
TEST_MOD_ZIP_NAME = 'test1.mod.zip'
TEST_IT_FILENAME = 'test2.it'
TEST_IT_ZIP_NAME = 'test2.it.zip'
TEST_S3M_FILENAME = 'test3.s3m'
TEST_S3M_ZIP_NAME = 'test3.s3m.zip'

class UploadViewAuthTests(TestCase):
    def test_upload_view_redirects_unauthenticated_user(self):
        # Arrange
        upload_url = reverse('upload_songs')
        login_url = reverse('login')

        # Act
        response = self.client.get(upload_url)

        # Assert
        self.assertRedirects(response, f"{login_url}?next={upload_url}")

    def test_upload_view_permits_authenticated_user(self):
        # Arrange
        user = factories.UserFactory()
        self.client.force_login(user)

        # Act
        response = self.client.get(reverse('upload_songs'))

        # Assert
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, "upload.html")

class UploadViewTests(TestCase):
    test_mod_info = {
        'format': 'MOD',
        'channels': 4,
        'name': SONG_TITLE
    }

    test_s3m_info = {
        'format': 'S3M',
        'channels': 16,
        'name': S3M_TITLE
    }

    test_it_info = {
        'format': 'IT',
        'channels': 32,
        'name': IT_TITLE
    }

    temp_upload_dir = settings.TEMP_UPLOAD_DIR
    new_file_dir = settings.NEW_FILE_DIR

    def setUp(self):
        self.user = factories.UserFactory()
        self.client.force_login(self.user)

    def tearDown(self):
        # Cleanup new_file_dir after each test
        for filename in os.listdir(self.new_file_dir):
            file_path = os.path.join(self.new_file_dir, filename)
            os.remove(file_path)

    def assert_zipped_file(self, new_file_dir, zipped_filename, unzipped_filename):
        # Verify that a zip file has been added
        self.assertTrue(os.path.isfile(os.path.join(new_file_dir, zipped_filename)))

        # Open the zip file and get the list of files inside
        with zipfile.ZipFile(os.path.join(new_file_dir, zipped_filename), 'r') as zip_file:
            file_list = zip_file.namelist()

        # Verify that the zip file contains the original song
        self.assertEqual(len(file_list), 1)
        self.assertEqual(file_list[0], unzipped_filename)

    def assert_song_in_database(self, filename, title, song_format, channels, profile, is_by_uploader):
        new_song = NewSong.objects.get(filename=filename)
        self.assertEqual(title, new_song.title)
        self.assertEqual(song_format, new_song.format)
        self.assertEqual(channels, new_song.channels)
        self.assertEqual(profile, new_song.uploader_profile)
        self.assertEqual(is_by_uploader, new_song.is_by_uploader)
        self.assertEqual(filename, new_song.filename_unzipped)

    def assert_context_success(self, context, total_expected, filenames, titles, formats):
        self.assertIn('successful_files', context)
        successful_files = context['successful_files']
        self.assertEqual(len(successful_files), total_expected)

        # Create sets of expected files and successful files
        expected_set = set((filename, title, file_format) for filename, title, file_format in zip(filenames, titles, formats))
        successful_set = set((file['filename'], file['title'], file['format']) for file in successful_files)

        # Check if the sets are equal, meaning the order doesn't matter
        self.assertEqual(expected_set, successful_set)

    def create_file(self, filename, actual_filename=None):
        if actual_filename:
            file_path = self.get_file_path(actual_filename)
        else:
            file_path = self.get_file_path(filename)

        with open(file_path, 'rb') as f:
            file_data = f.read()

        return SimpleUploadedFile(filename, file_data, content_type=OCTET_STREAM)

    def get_file_path(self, filename):
        return os.path.join(os.path.dirname(__file__), '../../testdata', filename)

    @patch('uploads.views.upload_view.get_mod_info')
    def test_upload_single_song(self, mock_mod_info):
        # Arrange
        mock_mod_info.return_value = self.test_mod_info
        uploaded_file = self.create_file(TEST_MOD_FILENAME)

        # Act
        response = self.client.post(reverse('upload_songs'), {
            'written_by_me': 'yes',
            'song_file': uploaded_file
        })

        # Assert
        self.assert_zipped_file(self.new_file_dir, TEST_MOD_ZIP_NAME, TEST_MOD_FILENAME)
        self.assertEqual(os.listdir(self.temp_upload_dir), [])
        self.assert_song_in_database(TEST_MOD_FILENAME, SONG_TITLE, Song.Formats.MOD, 4, self.user.profile, True)
        self.assert_context_success(response.context, 1, [TEST_MOD_FILENAME], [SONG_TITLE], [Song.Formats.MOD])

    @patch('uploads.views.upload_view.get_mod_info')
    def test_upload_multiple_songs(self, mock_mod_info):
        # Arrange
        mod_path = self.get_file_path(TEST_MOD_FILENAME)
        it_path = self.get_file_path(TEST_IT_FILENAME)
        s3m_path = self.get_file_path(TEST_S3M_FILENAME)

        responses = [
            self.test_mod_info,
            self.test_it_info,
            self.test_s3m_info,
        ]

        mock_mod_info.side_effect = responses

        with tempfile.TemporaryDirectory() as temp_dir:
            zip_file_path = os.path.join(temp_dir, 'test.zip')

            with zipfile.ZipFile(zip_file_path, 'w') as zip_file:
                zip_file.write(mod_path, arcname=TEST_MOD_FILENAME)
                zip_file.write(it_path, arcname=TEST_IT_FILENAME)
                zip_file.write(s3m_path, arcname=TEST_S3M_FILENAME)

            # Act
            with open(zip_file_path, 'rb') as f:
                response = self.client.post(reverse('upload_songs'), {'written_by_me': 'no', 'song_file': f})

            # Assert
            self.assert_zipped_file(self.new_file_dir, TEST_MOD_ZIP_NAME, TEST_MOD_FILENAME)
            self.assert_zipped_file(self.new_file_dir, TEST_IT_ZIP_NAME, TEST_IT_FILENAME)
            self.assert_zipped_file(self.new_file_dir, TEST_S3M_ZIP_NAME, TEST_S3M_FILENAME)

            self.assertEqual(len(os.listdir(self.temp_upload_dir)), 0)

            self.assert_song_in_database(TEST_MOD_FILENAME, SONG_TITLE, Song.Formats.MOD, 4, self.user.profile, False)
            self.assert_song_in_database(TEST_IT_FILENAME, IT_TITLE, Song.Formats.IT, 32, self.user.profile, False)
            self.assert_song_in_database(TEST_S3M_FILENAME, S3M_TITLE, Song.Formats.S3M, 16, self.user.profile, False)

            self.assert_context_success(response.context, 3, [TEST_MOD_FILENAME, TEST_IT_FILENAME, TEST_S3M_FILENAME], [SONG_TITLE, IT_TITLE, S3M_TITLE], [Song.Formats.MOD, Song.Formats.IT, Song.Formats.S3M])

    @patch('uploads.views.upload_view.get_mod_info')
    def test_reject_files_already_in_screening(self, mock_mod_info):
        # Arrange
        mock_mod_info.return_value = self.test_mod_info
        upload_factories.NewSongFactory(hash='47c9d81e6c4966913e068a84b1b340f6', uploader_profile=self.user.profile)
        uploaded_file = self.create_file(TEST_MOD_FILENAME)

        # Act
        response = self.client.post(reverse('upload_songs'), {
            'written_by_me': 'yes',
            'song_file': uploaded_file
        })

        # Assert
        self.assertFalse(os.path.isfile(os.path.join(self.new_file_dir, TEST_MOD_FILENAME)))

        self.assertIn('successful_files', response.context)
        successful_files = response.context['successful_files']
        self.assertEqual(len(successful_files), 0)

        self.assertIn('failed_files', response.context)
        failed_files = response.context['failed_files']
        self.assertEqual(len(failed_files), 1)
        failed_file = failed_files[0]
        self.assertEqual(failed_file['filename'], TEST_MOD_FILENAME)
        self.assertEqual(failed_file['reason'], constants.UPLOAD_DUPLICATE_SONG_IN_PROCESSING_QUEUE)

    @patch('uploads.views.upload_view.get_mod_info')
    def test_reject_files_already_in_archive(self, mock_mod_info):
        # Arrange
        mock_mod_info.return_value = self.test_mod_info
        song_factories.SongFactory(hash='47c9d81e6c4966913e068a84b1b340f6')
        uploaded_file = self.create_file(TEST_MOD_FILENAME)

        # Act
        response = self.client.post(reverse('upload_songs'), {
            'written_by_me': 'yes',
            'song_file': uploaded_file
        })

        # Assert
        self.assertFalse(os.path.isfile(os.path.join(self.new_file_dir, TEST_MOD_FILENAME)))

        self.assertIn('successful_files', response.context)
        successful_files = response.context['successful_files']
        self.assertEqual(len(successful_files), 0)

        self.assertIn('failed_files', response.context)
        failed_files = response.context['failed_files']
        self.assertEqual(len(failed_files), 1)
        failed_file = failed_files[0]
        self.assertEqual(failed_file['filename'], TEST_MOD_FILENAME)
        self.assertEqual(failed_file['reason'], constants.UPLOAD_DUPLICATE_SONG_IN_ARCHIVE)

    @override_settings(MAXIMUM_UPLOAD_SIZE=1000)
    @patch('uploads.views.upload_view.get_mod_info')
    def test_reject_files_that_are_too_large(self, mock_mod_info):
        # Arrange
        mock_mod_info.return_value = self.test_mod_info
        uploaded_file = self.create_file(TEST_MOD_FILENAME)

        # Act
        response = self.client.post(reverse('upload_songs'), {
            'written_by_me': 'yes',
            'song_file': uploaded_file
        })

        # Assert
        self.assertFalse(os.path.isfile(os.path.join(self.new_file_dir, TEST_MOD_FILENAME)))

        self.assertIn('successful_files', response.context)
        successful_files = response.context['successful_files']
        self.assertEqual(len(successful_files), 0)

        self.assertIn('failed_files', response.context)
        failed_files = response.context['failed_files']
        self.assertEqual(len(failed_files), 1)
        failed_file = failed_files[0]
        self.assertEqual(failed_file['filename'], TEST_MOD_FILENAME)
        self.assertEqual(failed_file['reason'], constants.UPLOAD_TOO_LARGE%(settings.MAXIMUM_UPLOAD_SIZE))

    @override_settings(MAXIMUM_UPLOAD_FILENAME_LENGTH=4)
    @patch('uploads.views.upload_view.get_mod_info')
    def test_reject_file_with_long_filename(self, mock_mod_info):
        # Arrange
        mock_mod_info.return_value = self.test_mod_info
        uploaded_file = self.create_file(TEST_MOD_FILENAME)

        # Act
        response = self.client.post(reverse('upload_songs'), {
            'written_by_me': 'yes',
            'song_file': uploaded_file
        })

        # Assert
        self.assertFalse(os.path.isfile(os.path.join(self.new_file_dir, TEST_MOD_FILENAME)))

        self.assertIn('successful_files', response.context)
        successful_files = response.context['successful_files']
        self.assertEqual(len(successful_files), 0)

        self.assertIn('failed_files', response.context)
        failed_files = response.context['failed_files']
        self.assertEqual(len(failed_files), 1)
        failed_file = failed_files[0]
        self.assertEqual(failed_file['filename'], TEST_MOD_FILENAME)
        self.assertEqual(failed_file['reason'], constants.UPLOAD_FILENAME_TOO_LONG%(settings.MAXIMUM_UPLOAD_FILENAME_LENGTH))

    @patch('uploads.views.upload_view.get_mod_info')
    def test_reject_file_when_modinfo_fails(self, mock_mod_info):
        # Arrange
        mock_mod_info.return_value = None
        uploaded_file = self.create_file(NOT_A_MOD_FILENAME)

        # Act
        response = self.client.post(reverse('upload_songs'), {
            'written_by_me': 'yes',
            'song_file': uploaded_file
        })

        # Assert
        self.assertFalse(os.path.isfile(os.path.join(self.new_file_dir, NOT_A_MOD_FILENAME)))

        self.assertIn('successful_files', response.context)
        successful_files = response.context['successful_files']
        self.assertEqual(len(successful_files), 0)

        self.assertIn('failed_files', response.context)
        failed_files = response.context['failed_files']
        self.assertEqual(len(failed_files), 1)
        failed_file = failed_files[0]
        self.assertEqual(failed_file['filename'], NOT_A_MOD_FILENAME)
        self.assertEqual(failed_file['reason'], constants.UPLOAD_UNRECOGNIZED_FORMAT)

    @override_settings(UNSUPPORTED_FORMATS=['it'])
    @patch('uploads.views.upload_view.get_mod_info')
    def test_reject_file_if_format_not_supported(self, mock_mod_info):
        # Arrange
        mock_mod_info.return_value = self.test_it_info
        uploaded_file = self.create_file(TEST_IT_FILENAME)

        # Act
        response = self.client.post(reverse('upload_songs'), {
            'written_by_me': 'yes',
            'song_file': uploaded_file
        })

        # Assert
        self.assertFalse(os.path.isfile(os.path.join(self.new_file_dir, TEST_IT_FILENAME)))

        self.assertIn('successful_files', response.context)
        successful_files = response.context['successful_files']
        self.assertEqual(len(successful_files), 0)

        self.assertIn('failed_files', response.context)
        failed_files = response.context['failed_files']
        self.assertEqual(len(failed_files), 1)
        failed_file = failed_files[0]
        self.assertEqual(failed_file['filename'], TEST_IT_FILENAME)
        self.assertEqual(failed_file['reason'], constants.UPLOAD_UNSUPPORTED_FORMAT)

    @patch('uploads.views.upload_view.get_mod_info')
    def test_rename_file_extension_when_it_does_not_match_the_format(self, mock_mod_info):
        # Arrange
        mock_mod_info.return_value = self.test_mod_info
        uploaded_file = self.create_file('test1.xm', TEST_MOD_FILENAME)

        # Act
        response = self.client.post(reverse('upload_songs'), {
            'written_by_me': 'yes',
            'song_file': uploaded_file
        })

        # Assert
        self.assert_zipped_file(self.new_file_dir, TEST_MOD_ZIP_NAME, TEST_MOD_FILENAME)
        self.assertEqual(os.listdir(self.temp_upload_dir), [])
        self.assert_song_in_database(TEST_MOD_FILENAME, SONG_TITLE, Song.Formats.MOD, 4, self.user.profile, True)
        self.assert_context_success(response.context, 1, [TEST_MOD_FILENAME], [SONG_TITLE], [Song.Formats.MOD])

    @patch('uploads.views.upload_view.get_mod_info')
    def test_rename_file_to_remove_whitespace_and_uppercase_letters(self, mock_mod_info):
        # Arrange
        mock_mod_info.return_value = self.test_mod_info
        uploaded_file = self.create_file('Test  1.mod', TEST_MOD_FILENAME)

        # Act
        response = self.client.post(reverse('upload_songs'), {
            'written_by_me': 'yes',
            'song_file': uploaded_file
        })

        # Assert
        underscored_mod_filename = 'test_1.mod'
        self.assert_zipped_file(self.new_file_dir, 'test_1.mod.zip', underscored_mod_filename)
        self.assertEqual(os.listdir(self.temp_upload_dir), [])
        self.assert_song_in_database(underscored_mod_filename, SONG_TITLE, Song.Formats.MOD, 4, self.user.profile, True)
        self.assert_context_success(response.context, 1, [underscored_mod_filename], [SONG_TITLE], [Song.Formats.MOD])

    @patch('uploads.views.upload_view.get_mod_info')
    def test_reject_file_if_previously_rejected_by_screeners(self, mock_mod_info):
        # Arrange
        uploaded_file = self.create_file(TEST_MOD_FILENAME)
        mock_mod_info.return_value = self.test_mod_info
        upload_factories.RejectedSongFactory(hash='47c9d81e6c4966913e068a84b1b340f6')

        # Act
        response = self.client.post(reverse('upload_songs'), {
            'written_by_me': 'yes',
            'song_file': uploaded_file
        })

        # Assert
        self.assertFalse(os.path.isfile(os.path.join(self.new_file_dir, TEST_MOD_FILENAME)))

        self.assertIn('successful_files', response.context)
        successful_files = response.context['successful_files']
        self.assertEqual(len(successful_files), 0)

        self.assertIn('failed_files', response.context)
        failed_files = response.context['failed_files']
        self.assertEqual(len(failed_files), 1)
        failed_file = failed_files[0]
        self.assertEqual(failed_file['filename'], TEST_MOD_FILENAME)
        self.assertEqual(failed_file['reason'], constants.UPLOAD_SONG_PREVIOUSLY_REJECTED)

    @patch('uploads.views.upload_view.get_mod_info')
    def test_permit_file_temporarily_rejected_by_screeners(self, mock_mod_info):
        # Arrange
        uploaded_file = self.create_file(TEST_MOD_FILENAME)
        mock_mod_info.return_value = self.test_mod_info
        upload_factories.RejectedSongFactory(hash='47c9d81e6c4966913e068a84b1b340f6', is_temporary=True)

        # Act
        response = self.client.post(reverse('upload_songs'), {
            'written_by_me': 'yes',
            'song_file': uploaded_file
        })

        # Assert
        self.assert_zipped_file(self.new_file_dir, TEST_MOD_ZIP_NAME, TEST_MOD_FILENAME)
        self.assertEqual(os.listdir(self.temp_upload_dir), [])
        self.assert_song_in_database(TEST_MOD_FILENAME, SONG_TITLE, Song.Formats.MOD, 4, self.user.profile, True)
        self.assert_context_success(response.context, 1, [TEST_MOD_FILENAME], [SONG_TITLE], [Song.Formats.MOD])
