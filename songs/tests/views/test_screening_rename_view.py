import zipfile
import os

from django.test import TestCase
from django.urls.base import reverse
from django.contrib.auth.models import Permission
from django.contrib.messages import get_messages
from django.conf import settings

from homepage.tests import factories
from songs import factories as songs_factories
from songs import constants, forms
from songs.models import NewSong

SCREENING_TEMPLATE = "screening_rename.html"
OLD_FILENAME = 'old_filename.mod'
NEW_FILENAME = 'new_filename.mod'

class ScreeningRenameAuthenticationTests(TestCase):
    def test_unauthenticated_user_is_redirected_to_login(self):
        # Arrange
        login_url = reverse('login')
        screening_url = reverse('screening_rename', kwargs={'pk': 1})

        # Act
        response = self.client.get(screening_url)

        # Assert
        self.assertEqual(302, response.status_code)
        self.assertRedirects(response, f"{login_url}?next={screening_url}")

    def test_authenticated_user_without_permission_is_forbidden(self):
        # Arrange
        user = factories.UserFactory()
        self.client.force_login(user)

        # Act
        response = self.client.get(reverse('screening_rename', kwargs={'pk': 1}))

        # Assert
        self.assertEqual(403, response.status_code)

class ScreeningRenameGetTests(TestCase):
    def setUp(self) -> None:
        self.user = factories.UserFactory()
        permission = Permission.objects.get(codename='can_approve_songs')
        self.user.user_permissions.add(permission)
        self.client.force_login(self.user)

    def test_does_not_permit_user_to_rename_unclaimed_song(self):
        # Arrange
        song = songs_factories.NewSongFactory()

        # Act
        response = self.client.get(reverse('screening_rename', kwargs={'pk': song.id}))

        # Assert
        self.assertRedirects(response, reverse('screen_song', kwargs={'pk': song.id}))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(1, len(messages))
        self.assertEqual(constants.RENAME_SCREENING_REQUIRES_CLAIM, str(messages[0]))

    def test_renders_screening_rename_template(self):
        # Arrange
        song = songs_factories.NewSongFactory(claimed_by=self.user.profile)

        # Act
        response = self.client.get(reverse('screening_rename', kwargs={'pk': song.id}))

        # Assert
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, SCREENING_TEMPLATE)
        self.assertEqual(song, response.context['song'])
        self.assertIsInstance(response.context['form'], forms.RenameForm)
        # new_filename in form is initially set to the current filename
        self.assertEqual(song.filename, response.context['form'].initial['new_filename'])

class ScreeningRenamePostTests(TestCase):
    def setUp(self) -> None:
        self.user = factories.UserFactory()
        permission = Permission.objects.get(codename='can_approve_songs')
        self.user.user_permissions.add(permission)
        self.client.force_login(self.user)

    def test_does_not_permit_user_to_rename_unclaimed_song(self):
        # Arrange
        song = songs_factories.NewSongFactory()

        # Act
        response = self.client.post(reverse('screening_rename', kwargs={'pk': song.id}), data={'new_filename': 'new_filename'})

        # Assert
        self.assertRedirects(response, reverse('screen_song', kwargs={'pk': song.id}))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(1, len(messages))
        self.assertEqual(constants.RENAME_SCREENING_REQUIRES_CLAIM, str(messages[0]))

    def test_new_filename_cannot_be_blank(self):
        # Arrange
        song = songs_factories.NewSongFactory(claimed_by=self.user.profile)

        # Act
        response = self.client.post(reverse('screening_rename', kwargs={'pk': song.id}), data={'new_filename': ''})

        # Assert
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, SCREENING_TEMPLATE)
        self.assertEqual(song, response.context['song'])
        self.assertIsInstance(response.context['form'], forms.RenameForm)
        self.assertEqual(song.filename, response.context['form'].initial['new_filename'])
        self.assertTrue(response.context['form'].has_error('new_filename'))

    def test_cannot_change_file_extension(self):
        # Arrange
        song = songs_factories.NewSongFactory(claimed_by=self.user.profile, filename=OLD_FILENAME, format='mod')

        # Act
        response = self.client.post(reverse('screening_rename', kwargs={'pk': song.id}), data={'new_filename': 'new_filename.s3m'})

        # Assert
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, SCREENING_TEMPLATE)
        self.assertEqual(song, response.context['song'])
        self.assertIsInstance(response.context['form'], forms.RenameForm)
        self.assertEqual(song.filename, response.context['form'].initial['new_filename'])
        self.assertTrue(response.context['form'].has_error('new_filename'))
        self.assertEqual(constants.RENAME_CANNOT_CHANGE_FILE_EXTENSION, response.context['form'].errors['new_filename'][0])

    def test_filename_must_be_changed(self):
        # Arrange
        song = songs_factories.NewSongFactory(claimed_by=self.user.profile, filename=OLD_FILENAME, format='mod')

        # Act
        response = self.client.post(reverse('screening_rename', kwargs={'pk': song.id}), data={'new_filename': song.filename})

        # Assert
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, SCREENING_TEMPLATE)
        self.assertEqual(song, response.context['song'])
        self.assertIsInstance(response.context['form'], forms.RenameForm)
        self.assertEqual(song.filename, response.context['form'].initial['new_filename'])
        self.assertTrue(response.context['form'].has_error('new_filename'))
        self.assertEqual(constants.RENAME_MUST_BE_CHANGED, response.context['form'].errors['new_filename'][0])

    def test_filename_must_adhere_to_unix_filename_conventions(self):
        # Arrange
        song = songs_factories.NewSongFactory(claimed_by=self.user.profile, filename=OLD_FILENAME, format='mod')

        # Act
        response = self.client.post(reverse('screening_rename', kwargs={'pk': song.id}), data={'new_filename': 'new_filename/.mod'})

        # Assert
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, SCREENING_TEMPLATE)
        self.assertEqual(song, response.context['song'])
        self.assertIsInstance(response.context['form'], forms.RenameForm)
        self.assertEqual(song.filename, response.context['form'].initial['new_filename'])
        self.assertTrue(response.context['form'].has_error('new_filename'))
        self.assertEqual(constants.RENAME_INVALID_FILENAME, response.context['form'].errors['new_filename'][0])

    def test_filename_cannot_be_identical_to_another_song_in_screening_queue(self):
        # Arrange
        song = songs_factories.NewSongFactory(claimed_by=self.user.profile, filename=OLD_FILENAME, format='mod')
        songs_factories.NewSongFactory(filename=NEW_FILENAME, format='mod')

        # Act
        response = self.client.post(reverse('screening_rename', kwargs={'pk': song.id}), data={'new_filename': NEW_FILENAME})

        # Assert
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, SCREENING_TEMPLATE)
        self.assertEqual(song, response.context['song'])
        self.assertIsInstance(response.context['form'], forms.RenameForm)
        self.assertEqual(song.filename, response.context['form'].initial['new_filename'])
        self.assertTrue(response.context['form'].has_error('new_filename'))
        self.assertEqual(constants.RENAME_FILENAME_TAKEN, response.context['form'].errors['new_filename'][0])

    def test_filename_cannot_be_identical_to_another_song_in_archive(self):
        # Arrange
        song = songs_factories.NewSongFactory(claimed_by=self.user.profile, filename=OLD_FILENAME, format='mod')
        songs_factories.SongFactory(filename=NEW_FILENAME, format='mod')

        # Act
        response = self.client.post(reverse('screening_rename', kwargs={'pk': song.id}), data={'new_filename': NEW_FILENAME})

        # Assert
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, SCREENING_TEMPLATE)
        self.assertEqual(song, response.context['song'])
        self.assertIsInstance(response.context['form'], forms.RenameForm)
        self.assertEqual(song.filename, response.context['form'].initial['new_filename'])
        self.assertTrue(response.context['form'].has_error('new_filename'))
        self.assertEqual(constants.RENAME_FILENAME_TAKEN, response.context['form'].errors['new_filename'][0])

    def test_filename_cannot_be_identical_to_song_in_rejected_queue(self):
        # Arrange
        song = songs_factories.NewSongFactory(claimed_by=self.user.profile, filename=OLD_FILENAME, format='mod')
        songs_factories.RejectedSongFactory(filename=NEW_FILENAME, format='mod')

        # Act
        response = self.client.post(reverse('screening_rename', kwargs={'pk': song.id}), data={'new_filename': NEW_FILENAME})

        # Assert
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, SCREENING_TEMPLATE)
        self.assertEqual(song, response.context['song'])
        self.assertIsInstance(response.context['form'], forms.RenameForm)
        self.assertEqual(song.filename, response.context['form'].initial['new_filename'])
        self.assertTrue(response.context['form'].has_error('new_filename'))
        self.assertEqual(constants.RENAME_FILENAME_TAKEN, response.context['form'].errors['new_filename'][0])

    def test_filename_cannot_exceed_59_characters(self):
        # Arrange
        song = songs_factories.NewSongFactory(claimed_by=self.user.profile, filename=OLD_FILENAME, format='mod')

        # Act
        response = self.client.post(reverse('screening_rename', kwargs={'pk': song.id}), data={'new_filename': 'a' * 60})

        # Assert
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, SCREENING_TEMPLATE)
        self.assertEqual(song, response.context['song'])
        self.assertIsInstance(response.context['form'], forms.RenameForm)
        self.assertEqual(song.filename, response.context['form'].initial['new_filename'])
        self.assertTrue(response.context['form'].has_error('new_filename'))
        self.assertEqual("Ensure this value has at most 59 characters (it has 60).", response.context['form'].errors['new_filename'][0])

    def test_rename_is_successful(self):
        # Arrange
        new_file_dir = settings.NEW_FILE_DIR
        song = songs_factories.NewSongFactory(claimed_by=self.user.profile, filename=OLD_FILENAME, format='mod')

        # Create a zip file called old_filename.mod.zip with a file called old_filename.mod
        old_file_path = os.path.join(new_file_dir, OLD_FILENAME)
        with open(old_file_path, 'w', encoding='utf-8') as old_file:
            old_file.write('This is the content of the original file.')

        with zipfile.ZipFile(os.path.join(new_file_dir, f'{OLD_FILENAME}.zip'), 'w') as zip_file:
            zip_file.write(old_file_path, arcname=OLD_FILENAME)

        # Only the zip file should be in the path
        os.remove(old_file_path)

        # Act
        response = self.client.post(reverse('screening_rename', kwargs={'pk': song.id}), data={'new_filename': NEW_FILENAME})

        # Assert
        self.assertRedirects(response, reverse('screen_song', kwargs={'pk': song.id}))
        self.assertEqual(NEW_FILENAME, NewSong.objects.get(pk=song.id).filename)

        # Check that old_filename.mod.zip no longer exists in new_file_dir
        self.assertFalse(os.path.exists(os.path.join(new_file_dir, f'{OLD_FILENAME}.zip')))
        self.assertTrue(os.path.exists(os.path.join(new_file_dir, f'{NEW_FILENAME}.zip')))

        with zipfile.ZipFile(os.path.join(new_file_dir, f'{NEW_FILENAME}.zip'), 'r') as zip_file:
            # Extract the content of the zip file
            zip_file.extractall(new_file_dir)
            # Check that the zip file contains a file called new_filename.mod
            self.assertTrue(os.path.exists(os.path.join(new_file_dir, NEW_FILENAME)))
            # Check that the content of new_filename.mod is the same as the original file
            with open(os.path.join(new_file_dir, NEW_FILENAME), 'r', encoding='utf-8') as new_file:
                self.assertEqual(new_file.read(), 'This is the content of the original file.')
