from django.test import TestCase
from django.urls.base import reverse
from django.contrib.auth.models import Permission

from songs import factories as song_factories
from songs import constants
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

    def test_song_claimed_by_user_shows_claimed_by_me(self):
        # Arrange
        user = factories.UserFactory()
        permission = Permission.objects.get(codename='can_approve_songs')
        user.user_permissions.add(permission)
        song = song_factories.NewSongFactory(claimed_by=user.profile)
        self.client.force_login(user)

        # Act
        response = self.client.get(reverse('screen_song', kwargs = {'pk': song.id}))

        # Assert
        self.assertEqual(200, response.status_code)
        self.assertIn('claimed_by_me', response.context)
        self.assertTrue(response.context['claimed_by_me'])

    def test_song_claimed_by_other_user_shows_claimed_by_other_user(self):
        # Arrange
        user = factories.UserFactory()
        other_user = factories.UserFactory()
        permission = Permission.objects.get(codename='can_approve_songs')
        user.user_permissions.add(permission)
        song = song_factories.NewSongFactory(claimed_by=other_user.profile)
        self.client.force_login(user)

        # Act
        response = self.client.get(reverse('screen_song', kwargs = {'pk': song.id}))

        # Assert
        self.assertEqual(200, response.status_code)
        self.assertIn('claimed_by_me', response.context)
        self.assertFalse(response.context['claimed_by_me'])
        self.assertIn('claimed_by_other_user', response.context)
        self.assertTrue(response.context['claimed_by_other_user'])

    def test_unclaimed_song_shows_claim_action(self):
        # Arrange
        user = factories.UserFactory()
        permission = Permission.objects.get(codename='can_approve_songs')
        user.user_permissions.add(permission)
        song = song_factories.NewSongFactory()
        self.client.force_login(user)

        # Act
        response = self.client.get(reverse('screen_song', kwargs = {'pk': song.id}))

        # Assert
        self.assertEqual(1, len(response.context['actions']))
        self.assertIn(constants.CLAIM_ACTION, response.context['actions'])

    def test_claimed_song_shows_permitted_actions(self):
        # Arrange
        user = factories.UserFactory()
        permission = Permission.objects.get(codename='can_approve_songs')
        user.user_permissions.add(permission)
        song = song_factories.NewSongFactory(claimed_by=user.profile)
        self.client.force_login(user)

        # Act
        response = self.client.get(reverse('screen_song', kwargs = {'pk': song.id}))

        # Assert
        self.assertEqual(5, len(response.context['actions']))
        self.assertIn(constants.PRE_SCREEN_ACTION, response.context['actions'])
        self.assertIn(constants.PRE_SCREEN_AND_RECOMMEND_ACTION, response.context['actions'])
        self.assertIn(constants.NEEDS_SECOND_OPINION_ACTION, response.context['actions'])
        self.assertIn(constants.POSSIBLE_DUPLICATE_ACTION, response.context['actions'])
        self.assertIn(constants.UNDER_INVESTIGATION_ACTION, response.context['actions'])

    def test_song_claimed_by_other_shows_no_actions(self):
        # Arrange
        user = factories.UserFactory()
        other_user = factories.UserFactory()
        permission = Permission.objects.get(codename='can_approve_songs')
        user.user_permissions.add(permission)
        song = song_factories.NewSongFactory(claimed_by=other_user.profile)
        self.client.force_login(user)

        # Act
        response = self.client.get(reverse('screen_song', kwargs = {'pk': song.id}))

        # Assert
        self.assertEqual(0, len(response.context['actions']))
