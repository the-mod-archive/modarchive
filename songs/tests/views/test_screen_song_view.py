from django.test import TestCase
from django.urls.base import reverse
from django.contrib.auth.models import Permission

from songs import factories as song_factories
from homepage.tests import factories

class ScreenSongViewTests(TestCase):
    def test_unauthenticated_user_is_redirected_to_login(self):
        # Arrange
        song = song_factories.NewSongFactory()
        login_url = reverse('login')
        screening_url = reverse('screen_song', kwargs = {'pk': song.id})

        # Act
        response = self.client.get(reverse('screen_song', kwargs = {'pk': song.id}))

        # Assert
        self.assertEqual(302, response.status_code)
        self.assertRedirects(response, f"{login_url}?next={screening_url}")

    def test_authenticated_user_without_permission_is_forbidden(self):
        # Arrange
        user = factories.UserFactory()
        song = song_factories.NewSongFactory()
        self.client.force_login(user)

        # Act
        response = self.client.get(reverse('screen_song', kwargs = {'pk': song.id}))

        # Assert
        self.assertEqual(403, response.status_code)

    def test_authenticated_user_with_permission_can_access(self):
        # Arrange
        user = factories.UserFactory()
        permission = Permission.objects.get(codename='can_approve_songs')
        user.user_permissions.add(permission)
        song = song_factories.NewSongFactory()
        self.client.force_login(user)

        # Act
        response = self.client.get(reverse('screen_song', kwargs = {'pk': song.id}))

        # Assert
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, "screen_song.html")
        self.assertIn('new_song', response.context)
