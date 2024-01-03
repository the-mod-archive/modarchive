import os
import tempfile
import zipfile

from django.conf import settings

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls.base import reverse

from homepage.tests import factories
from songs.models import Song, NewSong

from songs import factories as song_factories

OCTET_STREAM = 'application/octet-stream'
SONG_TITLE = 'Test Song'
NOT_A_MOD_FILENAME = 'not_a_mod.txt'

class UploadViewTests(TestCase):
    test_mod_filename = 'test1.mod'
    test_mod_zip_name = 'test1.mod.zip'
    test_it_filename = 'test2.it'
    test_it_zip_name = 'test2.it.zip'
    test_s3m_filename = 'test3.s3m'
    test_s3m_zip_name = 'test3.s3m.zip'

    def setUp(self):
        self.temp_upload_dir = settings.TEMP_UPLOAD_DIR
        self.new_file_dir = settings.NEW_FILE_DIR

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

    def assert_context_success(self, context, total_expected, filenames, titles, formats):
        self.assertIn('successful_files', context)
        successful_files = context['successful_files']
        self.assertEqual(len(successful_files), total_expected)

        for i in range(total_expected):
            successful_file = successful_files[i]
            self.assertEqual(successful_file['filename'], filenames[i])
            self.assertEqual(successful_file['title'], titles[i])
            self.assertEqual(successful_file['format'], formats[i])

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

    def test_upload_single_song(self):
        # Arrange
        user = factories.UserFactory()
        file_path = os.path.join(os.path.dirname(__file__), 'testdata', self.test_mod_filename)

        with open(file_path, 'rb') as f:
            file_data = f.read()
        uploaded_file = SimpleUploadedFile(self.test_mod_filename, file_data, content_type=OCTET_STREAM)

        self.client.force_login(user)

        # Act
        response = self.client.post(reverse('upload_songs'), {
            'written_by_me': 'yes',
            'song_file': uploaded_file
        })

        # Assert        
        self.assert_zipped_file(self.new_file_dir, self.test_mod_zip_name, self.test_mod_filename)
        self.assertEqual(os.listdir(self.temp_upload_dir), [])
        self.assert_song_in_database(self.test_mod_filename, SONG_TITLE, Song.Formats.MOD, 4, user.profile, True)
        self.assert_context_success(response.context, 1, [self.test_mod_filename], [SONG_TITLE], [Song.Formats.MOD])

    def test_upload_multiple_songs(self):
        # Arrange
        user = factories.UserFactory()
        self.client.force_login(user)

        mod_path = os.path.join(os.path.dirname(__file__), 'testdata', self.test_mod_filename)
        it_path = os.path.join(os.path.dirname(__file__), 'testdata', self.test_it_filename)
        s3m_path = os.path.join(os.path.dirname(__file__), 'testdata', self.test_s3m_filename)

        with tempfile.TemporaryDirectory() as temp_dir:
            zip_file_path = os.path.join(temp_dir, 'test.zip')

            with zipfile.ZipFile(zip_file_path, 'w') as zip_file:
                zip_file.write(mod_path, arcname=self.test_mod_filename)
                zip_file.write(it_path, arcname=self.test_it_filename)
                zip_file.write(s3m_path, arcname=self.test_s3m_filename)

            # Act
            with open(zip_file_path, 'rb') as f:
                response = self.client.post(reverse('upload_songs'), {'written_by_me': 'no', 'song_file': f})

            # Assert
            self.assert_zipped_file(self.new_file_dir, self.test_mod_zip_name, self.test_mod_filename)
            self.assert_zipped_file(self.new_file_dir, self.test_it_zip_name, self.test_it_filename)
            self.assert_zipped_file(self.new_file_dir, self.test_s3m_zip_name, self.test_s3m_filename)

            self.assertEqual(len(os.listdir(self.temp_upload_dir)), 0)

            self.assert_song_in_database(self.test_mod_filename, SONG_TITLE, Song.Formats.MOD, 4, user.profile, False)
            self.assert_song_in_database(self.test_it_filename, 'Test IT', Song.Formats.IT, 32, user.profile, False)
            self.assert_song_in_database(self.test_s3m_filename, 'Test S3M', Song.Formats.S3M, 16, user.profile, False)

            self.assert_context_success(response.context, 3, [self.test_mod_filename, self.test_it_filename, self.test_s3m_filename], [SONG_TITLE, 'Test IT', 'Test S3M'], [Song.Formats.MOD, Song.Formats.IT, Song.Formats.S3M])

    def test_reject_files_already_in_screening(self):
        # Arrange
        user = factories.UserFactory()
        file_path = os.path.join(os.path.dirname(__file__), 'testdata', self.test_mod_filename)

        song_factories.NewSongFactory(hash='47c9d81e6c4966913e068a84b1b340f6', uploader_profile=user.profile)

        with open(file_path, 'rb') as f:
            file_data = f.read()
        uploaded_file = SimpleUploadedFile(self.test_mod_filename, file_data, content_type=OCTET_STREAM)

        self.client.force_login(user)

        # Act
        response = self.client.post(reverse('upload_songs'), {
            'written_by_me': 'yes',
            'song_file': uploaded_file
        })

        # Assert
        self.assertFalse(os.path.isfile(os.path.join(self.new_file_dir, self.test_mod_filename)))
        
        self.assertIn('successful_files', response.context)
        successful_files = response.context['successful_files']
        self.assertEqual(len(successful_files), 0)

        self.assertIn('failed_files', response.context)
        failed_files = response.context['failed_files']
        self.assertEqual(len(failed_files), 1)
        failed_file = failed_files[0]
        self.assertEqual(failed_file['filename'], self.test_mod_filename)
        self.assertEqual(failed_file['reason'], 'An identical song was already found in the upload processing queue.')

    def test_reject_files_already_in_archive(self):
        # Arrange
        user = factories.UserFactory()
        file_path = os.path.join(os.path.dirname(__file__), 'testdata', self.test_mod_filename)

        song_factories.SongFactory(hash='47c9d81e6c4966913e068a84b1b340f6')

        with open(file_path, 'rb') as f:
            file_data = f.read()
        uploaded_file = SimpleUploadedFile(self.test_mod_filename, file_data, content_type=OCTET_STREAM)

        self.client.force_login(user)

        # Act
        response = self.client.post(reverse('upload_songs'), {
            'written_by_me': 'yes',
            'song_file': uploaded_file
        })

        # Assert
        self.assertFalse(os.path.isfile(os.path.join(self.new_file_dir, self.test_mod_filename)))
        
        self.assertIn('successful_files', response.context)
        successful_files = response.context['successful_files']
        self.assertEqual(len(successful_files), 0)

        self.assertIn('failed_files', response.context)
        failed_files = response.context['failed_files']
        self.assertEqual(len(failed_files), 1)
        failed_file = failed_files[0]
        self.assertEqual(failed_file['filename'], self.test_mod_filename)
        self.assertEqual(failed_file['reason'], 'An identical song was already found in the archive.')

    @override_settings(MAXIMUM_UPLOAD_SIZE=1000)
    def test_reject_files_that_are_too_large(self):
        # Arrange
        user = factories.UserFactory()
        file_path = os.path.join(os.path.dirname(__file__), 'testdata', self.test_mod_filename)

        with open(file_path, 'rb') as f:
            file_data = f.read()
        uploaded_file = SimpleUploadedFile(self.test_mod_filename, file_data, content_type=OCTET_STREAM)

        self.client.force_login(user)

        # Act
        response = self.client.post(reverse('upload_songs'), {
            'written_by_me': 'yes',
            'song_file': uploaded_file
        })

        # Assert
        self.assertFalse(os.path.isfile(os.path.join(self.new_file_dir, self.test_mod_filename)))

        self.assertIn('successful_files', response.context)
        successful_files = response.context['successful_files']
        self.assertEqual(len(successful_files), 0)

        self.assertIn('failed_files', response.context)
        failed_files = response.context['failed_files']
        self.assertEqual(len(failed_files), 1)
        failed_file = failed_files[0]
        self.assertEqual(failed_file['filename'], self.test_mod_filename)
        self.assertEqual(failed_file['reason'], f'The file was above the maximum allowed size of {settings.MAXIMUM_UPLOAD_SIZE} bytes.')

    @override_settings(MAXIMUM_UPLOAD_FILENAME_LENGTH=4)
    def test_reject_file_with_long_filename(self):
        # Arrange
        user = factories.UserFactory()
        file_path = os.path.join(os.path.dirname(__file__), 'testdata', self.test_mod_filename)

        with open(file_path, 'rb') as f:
            file_data = f.read()
        uploaded_file = SimpleUploadedFile(self.test_mod_filename, file_data, content_type=OCTET_STREAM)

        self.client.force_login(user)

        # Act
        response = self.client.post(reverse('upload_songs'), {
            'written_by_me': 'yes',
            'song_file': uploaded_file
        })

        # Assert
        self.assertFalse(os.path.isfile(os.path.join(self.new_file_dir, self.test_mod_filename)))

        self.assertIn('successful_files', response.context)
        successful_files = response.context['successful_files']
        self.assertEqual(len(successful_files), 0)

        self.assertIn('failed_files', response.context)
        failed_files = response.context['failed_files']
        self.assertEqual(len(failed_files), 1)
        failed_file = failed_files[0]
        self.assertEqual(failed_file['filename'], self.test_mod_filename)
        self.assertEqual(failed_file['reason'], f'The filename length was above the maximum allowed limit of {settings.MAXIMUM_UPLOAD_FILENAME_LENGTH} characters.')

    def test_reject_file_when_modinfo_fails(self):
        # Arrange
        user = factories.UserFactory()
        file_path = os.path.join(os.path.dirname(__file__), 'testdata', NOT_A_MOD_FILENAME)

        with open(file_path, 'rb') as f:
            file_data = f.read()
        uploaded_file = SimpleUploadedFile(NOT_A_MOD_FILENAME, file_data, content_type=OCTET_STREAM)

        self.client.force_login(user)

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
        self.assertEqual(failed_file['reason'], 'Did not recognize this file as a valid mod format.')

    @override_settings(UNSUPPORTED_FORMATS=['it'])
    def test_reject_file_if_format_not_supported(self):
        # Arrange
        user = factories.UserFactory()
        file_path = os.path.join(os.path.dirname(__file__), 'testdata', self.test_it_filename)

        with open(file_path, 'rb') as f:
            file_data = f.read()
        uploaded_file = SimpleUploadedFile(self.test_it_filename, file_data, content_type=OCTET_STREAM)

        self.client.force_login(user)

        # Act
        response = self.client.post(reverse('upload_songs'), {
            'written_by_me': 'yes',
            'song_file': uploaded_file
        })

        # Assert
        self.assertFalse(os.path.isfile(os.path.join(self.new_file_dir, self.test_it_filename)))

        self.assertIn('successful_files', response.context)
        successful_files = response.context['successful_files']
        self.assertEqual(len(successful_files), 0)

        self.assertIn('failed_files', response.context)
        failed_files = response.context['failed_files']
        self.assertEqual(len(failed_files), 1)
        failed_file = failed_files[0]
        self.assertEqual(failed_file['filename'], self.test_it_filename)
        self.assertEqual(failed_file['reason'], 'This format is not currently supported.')

    def test_rename_file_extension_when_it_does_not_match_the_format(self):
        # Arrange
        user = factories.UserFactory()
        file_path = os.path.join(os.path.dirname(__file__), 'testdata', self.test_mod_filename)

        with open(file_path, 'rb') as f:
            file_data = f.read()
        uploaded_file = SimpleUploadedFile('test1.xm', file_data, content_type=OCTET_STREAM)

        self.client.force_login(user)

        # Act
        response = self.client.post(reverse('upload_songs'), {
            'written_by_me': 'yes',
            'song_file': uploaded_file
        })

        # Assert        
        self.assert_zipped_file(self.new_file_dir, self.test_mod_zip_name, self.test_mod_filename)
        self.assertEqual(os.listdir(self.temp_upload_dir), [])
        self.assert_song_in_database(self.test_mod_filename, SONG_TITLE, Song.Formats.MOD, 4, user.profile, True)
        self.assert_context_success(response.context, 1, [self.test_mod_filename], [SONG_TITLE], [Song.Formats.MOD])

    def test_rename_file_to_remove_whitespace_and_uppercase_letters(self):
        # Arrange
        TEST_MOD_FILENAME = 'test_1.mod'
        user = factories.UserFactory()
        file_path = os.path.join(os.path.dirname(__file__), 'testdata', self.test_mod_filename)

        with open(file_path, 'rb') as f:
            file_data = f.read()
        uploaded_file = SimpleUploadedFile('Test  1.mod', file_data, content_type=OCTET_STREAM)

        self.client.force_login(user)

        # Act
        response = self.client.post(reverse('upload_songs'), {
            'written_by_me': 'yes',
            'song_file': uploaded_file
        })

        # Assert        
        self.assert_zipped_file(self.new_file_dir, 'test_1.mod.zip', TEST_MOD_FILENAME)
        self.assertEqual(os.listdir(self.temp_upload_dir), [])
        self.assert_song_in_database(TEST_MOD_FILENAME, SONG_TITLE, Song.Formats.MOD, 4, user.profile, True)
        self.assert_context_success(response.context, 1, [TEST_MOD_FILENAME], [SONG_TITLE], [Song.Formats.MOD])
