from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls.base import reverse

from homepage.tests import factories
from songs import factories as song_factories

class ScreeningActionViewTests(TestCase):
    def test_unauthenticated_user_is_redirected_to_login(self):
        # Arrange
        screening_url = reverse('screening_action')
        login_url = reverse('login')

        # Act
        response = self.client.post(reverse('screening_action'))

        # Assert
        self.assertEqual(302, response.status_code)
        self.assertRedirects(response, f"{login_url}?next={screening_url}")

    def test_user_without_permission_is_denied_access(self):
        # Arrange
        user = factories.UserFactory()

        # Act
        self.client.force_login(user)
        response = self.client.post(reverse('screening_action'))

        # Assert
        self.assertEqual(403, response.status_code)

    def test_authenticated_user_with_permission_can_post(self):
        # Arrange
        user = factories.UserFactory()
        permission = Permission.objects.get(codename='can_approve_songs')
        user.user_permissions.add(permission)

        # Act
        self.client.force_login(user)
        response = self.client.post(reverse('screening_action'))

        # Assert
        self.assertEqual(200, response.status_code)

    def test_action_result_shows_selected_songs(self):
        # Arrange
        user = factories.UserFactory()
        permission = Permission.objects.get(codename='can_approve_songs')
        user.user_permissions.add(permission)
        song1 = song_factories.NewSongFactory(filename='song1.mod', uploader_profile=user.profile)
        song2 = song_factories.NewSongFactory(filename='song2.mod', uploader_profile=user.profile)

        # Act
        self.client.force_login(user)
        response = self.client.post(reverse('screening_action'), {'selected_songs': [song1.id, song2.id], 'action': 'approve'})

        # Assert
        self.assertEqual(200, response.status_code)
        self.assertIn(song1, response.context['selected_songs'])
        self.assertIn(song2, response.context['selected_songs'])
        self.assertEqual(2, len(response.context['selected_songs']))
