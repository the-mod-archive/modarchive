from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls.base import reverse

from homepage.tests import factories
from songs import factories as song_factories

class ScreeningViewTests(TestCase):
    def test_screening_view_permits_access_to_authenticated_users(self):
        user = factories.UserFactory()
        permission = Permission.objects.get(codename='can_approve_songs')
        user.user_permissions.add(permission)
        self.client.force_login(user)

        response = self.client.get(reverse('screen_songs'))

        # Assert
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, "screening.html")

    def test_screening_view_rejects_access_to_unauthenticated_users(self):
        response = self.client.get(reverse('screen_songs'))
        screening_url = reverse('screen_songs')
        login_url = reverse('login')

        # Assert
        self.assertEqual(302, response.status_code)
        self.assertRedirects(response, f"{login_url}?next={screening_url}")

    def test_screening_view_rejects_access_to_users_with_insufficient_permissions(self):
        user = factories.UserFactory()
        self.client.force_login(user)

        response = self.client.get(reverse('screen_songs'))

        # Assert
        self.assertEqual(403, response.status_code)

    def test_screening_view_contains_new_songs(self):
        user = factories.UserFactory()
        permission = Permission.objects.get(codename='can_approve_songs')
        user.user_permissions.add(permission)
        self.client.force_login(user)

        song = song_factories.NewSongFactory(filename='song1.mod', uploader_profile=user.profile)

        response = self.client.get(reverse('screen_songs'))

        # Assert
        self.assertIn(song, response.context['new_songs'])
        self.assertEqual(len(response.context['new_songs']), 1)

    def test_screening_view_filters_high_priority_songs(self):
        uploading_user = factories.UserFactory()
        user = factories.UserFactory()
        permission = Permission.objects.get(codename='can_approve_songs')
        user.user_permissions.add(permission)
        self.client.force_login(user)

        high_priority_song_1 = song_factories.NewSongFactory(uploader_profile=uploading_user.profile)
        high_priority_song_2 = song_factories.NewSongFactory(uploader_profile=uploading_user.profile)
        low_priority_song_1 = song_factories.NewSongFactory(uploader_profile=None)
        low_priority_song_2 = song_factories.NewSongFactory(uploader_profile=None)

        response = self.client.get(f"{reverse('screen_songs')}?filter=high_priority")

        # Assert
        self.assertIn(high_priority_song_1, response.context['new_songs'])
        self.assertIn(high_priority_song_2, response.context['new_songs'])
        self.assertNotIn(low_priority_song_1, response.context['new_songs'])
        self.assertNotIn(low_priority_song_2, response.context['new_songs'])
        self.assertEqual(len(response.context['new_songs']), 2)

    def test_screening_view_filters_low_priority_songs(self):
        uploading_user = factories.UserFactory()
        user = factories.UserFactory()
        permission = Permission.objects.get(codename='can_approve_songs')
        user.user_permissions.add(permission)
        self.client.force_login(user)

        high_priority_song_1 = song_factories.NewSongFactory(uploader_profile=uploading_user.profile)
        high_priority_song_2 = song_factories.NewSongFactory(uploader_profile=uploading_user.profile)
        low_priority_song_1 = song_factories.NewSongFactory(uploader_profile=None)
        low_priority_song_2 = song_factories.NewSongFactory(uploader_profile=None)

        response = self.client.get(f"{reverse('screen_songs')}?filter=low_priority")

        # Assert
        self.assertIn(low_priority_song_1, response.context['new_songs'])
        self.assertIn(low_priority_song_2, response.context['new_songs'])
        self.assertNotIn(high_priority_song_1, response.context['new_songs'])
        self.assertNotIn(high_priority_song_2, response.context['new_songs'])
        self.assertEqual(len(response.context['new_songs']), 2)

    def test_screening_view_filters_songs_by_uploader(self):
        uploading_user = factories.UserFactory()
        user = factories.UserFactory()
        permission = Permission.objects.get(codename='can_approve_songs')
        user.user_permissions.add(permission)
        self.client.force_login(user)

        song_factories.NewSongFactory(uploader_profile=uploading_user.profile)
        high_priority_song_2 = song_factories.NewSongFactory(uploader_profile=uploading_user.profile, is_by_uploader=True)
        song_factories.NewSongFactory(uploader_profile=None)
        song_factories.NewSongFactory(uploader_profile=None)

        response = self.client.get(f"{reverse('screen_songs')}?filter=by_uploader")

        # Assert
        self.assertIn(high_priority_song_2, response.context['new_songs'])
        self.assertEqual(len(response.context['new_songs']), 1)

    def test_screening_view_shows_all_songs_by_default(self):
        uploading_user = factories.UserFactory()
        user = factories.UserFactory()
        permission = Permission.objects.get(codename='can_approve_songs')
        user.user_permissions.add(permission)
        self.client.force_login(user)

        high_priority_song_1 = song_factories.NewSongFactory(uploader_profile=uploading_user.profile)
        high_priority_song_2 = song_factories.NewSongFactory(uploader_profile=uploading_user.profile)
        low_priority_song_1 = song_factories.NewSongFactory(uploader_profile=None)
        low_priority_song_2 = song_factories.NewSongFactory(uploader_profile=None)

        response = self.client.get(f"{reverse('screen_songs')}")

        # Assert
        self.assertIn(high_priority_song_1, response.context['new_songs'])
        self.assertIn(high_priority_song_2, response.context['new_songs'])
        self.assertIn(low_priority_song_1, response.context['new_songs'])
        self.assertIn(low_priority_song_2, response.context['new_songs'])
        self.assertEqual(len(response.context['new_songs']), 4)
