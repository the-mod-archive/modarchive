from django.conf import settings
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls.base import reverse

from homepage.tests import factories
from songs import factories as song_factories

class ScreeningDownloadViewTests(TestCase):
    def test_screening_download_view_requires_authentication(self):
        # Arrange
        song = song_factories.NewSongFactory()
        login_url = reverse('login')
        screening_url = reverse('screening_download', kwargs = {'pk': song.id})

        # Act
        response = self.client.get(reverse('screening_download', kwargs = {'pk': song.id}))

        # Assert
        self.assertEqual(302, response.status_code)
        self.assertRedirects(response, f"{login_url}?next={screening_url}")

    def test_screening_download_view_requires_permission(self):
        # Arrange
        user = factories.UserFactory()
        song = song_factories.NewSongFactory()
        self.client.force_login(user)

        # Act
        response = self.client.get(reverse('screening_download', kwargs = {'pk': song.id}))

        # Assert
        self.assertEqual(403, response.status_code)

    def test_screening_download_view_returns_404_if_file_not_found(self):
        # Arrange
        user = factories.UserFactory()
        permission = Permission.objects.get(codename='can_approve_songs')
        user.user_permissions.add(permission)
        song = song_factories.NewSongFactory()
        self.client.force_login(user)

        # Act
        response = self.client.get(reverse('screening_download', kwargs = {'pk': song.id}))

        # Assert
        self.assertEqual(404, response.status_code)

    def test_screening_download_view_downloads_song(self):
        # Arrange
        user = factories.UserFactory()
        permission = Permission.objects.get(codename='can_approve_songs')
        user.user_permissions.add(permission)
        song = song_factories.NewSongFactory(filename='test.mod')
        self.client.force_login(user)

        new_file_dir = settings.NEW_FILE_DIR
        # Put a file in the new_file_dir called test.mod.zip - doesn't matter what it contains
        with open(f'{new_file_dir}/test.mod.zip', 'w', encoding='utf-8') as file:
            file.write('test')

        # Act
        response = self.client.get(reverse('screening_download', kwargs = {'pk': song.id}))

        # Assert
        self.assertEqual(200, response.status_code)
        self.assertEqual('application/force-download', response['Content-Type'])
        self.assertEqual(f'attachment; filename="{song.filename}.zip"', response['Content-Disposition'])
