from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from songs import factories as song_factories
from homepage.tests import factories

class NewSongListViewTest(TestCase):
    def test_new_songs_view_rejects_unauthenticated_user(self):
        # Arrange
        url = reverse('view_new_songs')

        # Act
        response = self.client.get(url)

        # Assert that unauthenticated users are redirected to the login page (HTTP 302)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/login/?next=/songs/view_new_songs')

    def test_new_songs_view_rejects_users_without_permission(self):
        # Arrange
        user = factories.UserFactory()
        song_factories.NewSongFactory(filename='song1.mod', uploader_profile=user.profile)

        # Act
        self.client.force_login(user)
        url = reverse('view_new_songs')
        response = self.client.get(url)

        # Assert that users without the permission are denied access (HTTP 403)
        self.assertEqual(response.status_code, 403)

    def test_authorized_user_can_view_song_list(self):
        # Arrange
        user = factories.UserFactory()
        permission = Permission.objects.get(codename='can_approve_songs')
        user.user_permissions.add(permission)
        song = song_factories.NewSongFactory(filename='song1.mod', uploader_profile=user.profile)

        # Act
        self.client.force_login(user)
        url = reverse('view_new_songs')
        response = self.client.get(url)

        # Assert that users with the permission can access the view (HTTP 200)
        self.assertEqual(response.status_code, 200)
        # Assert that the song is in the response context
        self.assertIn(song, response.context['new_songs'])
        self.assertEqual(len(response.context['new_songs']), 1)
