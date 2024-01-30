from django.test import TestCase
from django.urls.base import reverse
from django.contrib.auth.models import Permission
from django.contrib.messages import get_messages

from homepage.tests import factories
from songs import factories as songs_factories
from songs import constants

class ScreeningRejectAuthenticationTests(TestCase):
    def test_unauthenticated_user_is_redirected_to_login(self):
        # Arrange
        login_url = reverse('login')
        screening_url = reverse('screening_reject')

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
        response = self.client.get(reverse('screening_reject'))

        # Assert
        self.assertEqual(403, response.status_code)

    def test_authenticated_user_with_permission_can_access(self):
        # Arrange
        user = factories.UserFactory()
        permission = Permission.objects.get(codename='can_approve_songs')
        user.user_permissions.add(permission)
        self.client.force_login(user)
        song = songs_factories.NewSongFactory(claimed_by=user.profile)

        # Act
        response = self.client.get(f"{reverse('screening_reject')}?song_ids={song.id}")

        # Assert
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, "screening_reject.html")

class ScreeningRejectGetValidationTests(TestCase):
    def setUp(self):
        self.user = factories.UserFactory()
        permission = Permission.objects.get(codename='can_approve_songs')
        self.user.user_permissions.add(permission)
        self.client.force_login(self.user)

    def test_get_request_without_song_ids_redirects_to_screening_index(self):
        # Act
        response = self.client.get(reverse('screening_reject'))

        # Assert
        self.assertRedirects(response, reverse('screening_index'))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(1, len(messages))
        self.assertEqual(constants.REJECTION_REQUIRES_IDS, str(messages[0]))

    def test_songs_must_all_be_claimed_by_current_user(self):
        # Arrange
        song = songs_factories.NewSongFactory(claimed_by=None)
        song_2 = songs_factories.NewSongFactory(claimed_by=self.user.profile)

        # Act
        response = self.client.get(f"{reverse('screening_reject')}?song_ids={song.id},{song_2.id}")

        # Assert
        self.assertRedirects(response, reverse('screening_index'))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(1, len(messages))
        self.assertEqual(constants.REJECTION_ALL_SONGS_MUST_BE_CLAIMED, str(messages[0]))

    def test_renders_template_if_all_songs_are_claimed(self):
        # Arrange
        song = songs_factories.NewSongFactory(claimed_by=self.user.profile)
        song_2 = songs_factories.NewSongFactory(claimed_by=self.user.profile)

        # Act
        response = self.client.get(f"{reverse('screening_reject')}?song_ids={song.id},{song_2.id}")

        # Assert
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, "screening_reject.html")

    def test_song_ids_param_must_be_in_correct_format(self):
        # Act
        response = self.client.get(f"{reverse('screening_reject')}?song_ids=a,2")

        # Assert
        self.assertRedirects(response, reverse('screening_index'))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(1, len(messages))
        self.assertEqual(constants.REJECTION_REQUIRES_IDS, str(messages[0]))

    def test_if_song_ids_do_not_exist_redirect_to_screening_index(self):
        # Act
        response = self.client.get(f"{reverse('screening_reject')}?song_ids=1,2")

        # Assert
        self.assertRedirects(response, reverse('screening_index'))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(1, len(messages))
        self.assertEqual(constants.REJECTION_REQUIRES_IDS, str(messages[0]))


class ScreeningRejectPostValidationTests(TestCase):
    def setUp(self):
        self.user = factories.UserFactory()
        permission = Permission.objects.get(codename='can_approve_songs')
        self.user.user_permissions.add(permission)
        self.client.force_login(self.user)

    def test_post_request_without_song_ids_redirects_to_screening_index(self):
        # Act
        response = self.client.post(reverse('screening_reject'), data={})

        # Assert
        self.assertRedirects(response, reverse('screening_index'))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(1, len(messages))
        self.assertEqual(constants.REJECTION_REQUIRES_IDS, str(messages[0]))

    def test_song_ids_must_be_in_correct_format(self):
        # Act
        response = self.client.post(reverse('screening_reject'), data={'song_ids': 'a,2'})

        # Assert
        self.assertRedirects(response, reverse('screening_index'))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(1, len(messages))
        self.assertEqual(constants.REJECTION_REQUIRES_IDS, str(messages[0]))

    def test_songs_must_all_be_claimed_by_current_user(self):
        # Arrange
        song = songs_factories.NewSongFactory(claimed_by=None)
        song_2 = songs_factories.NewSongFactory(claimed_by=self.user.profile)

        # Act
        response = self.client.post(reverse('screening_reject'), data={'song_ids': f"{song.id},{song_2.id}"})

        # Assert
        self.assertRedirects(response, reverse('screening_index'))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(1, len(messages))
        self.assertEqual(constants.REJECTION_ALL_SONGS_MUST_BE_CLAIMED, str(messages[0]))

    def test_if_song_ids_do_not_exist_redirect_to_screening_index(self):
        # Act
        response = self.client.post(reverse('screening_reject'), data={'song_ids': '1,2'})

        # Assert
        self.assertRedirects(response, reverse('screening_index'))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(1, len(messages))
        self.assertEqual(constants.REJECTION_REQUIRES_IDS, str(messages[0]))
