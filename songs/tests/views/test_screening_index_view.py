from datetime import timedelta
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls.base import reverse
from django.utils import timezone

from homepage.tests import factories
from songs import factories as song_factories
from songs.models import NewSong

class ScreeningIndexViewTests(TestCase):
    def test_screening_view_permits_access_to_authenticated_users(self):
        user = factories.UserFactory()
        permission = Permission.objects.get(codename='can_approve_songs')
        user.user_permissions.add(permission)
        self.client.force_login(user)

        response = self.client.get(reverse('screening_index'))

        # Assert
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, "screening.html")

    def test_screening_view_rejects_access_to_unauthenticated_users(self):
        response = self.client.get(reverse('screening_index'))
        screening_url = reverse('screening_index')
        login_url = reverse('login')

        # Assert
        self.assertEqual(302, response.status_code)
        self.assertRedirects(response, f"{login_url}?next={screening_url}")

    def test_screening_view_rejects_access_to_users_with_insufficient_permissions(self):
        user = factories.UserFactory()
        self.client.force_login(user)

        response = self.client.get(reverse('screening_index'))

        # Assert
        self.assertEqual(403, response.status_code)

    def test_screening_view_contains_new_songs(self):
        user = factories.UserFactory()
        permission = Permission.objects.get(codename='can_approve_songs')
        user.user_permissions.add(permission)
        self.client.force_login(user)

        song = song_factories.NewSongFactory(filename='song1.mod', uploader_profile=user.profile)

        response = self.client.get(reverse('screening_index'))

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
        claimed_high_priority_song = song_factories.NewSongFactory(uploader_profile=uploading_user.profile, claimed_by=user.profile)

        response = self.client.get(f"{reverse('screening_index')}?filter=high_priority")

        # Assert
        self.assertIn(high_priority_song_1, response.context['new_songs'])
        self.assertIn(high_priority_song_2, response.context['new_songs'])
        self.assertNotIn(low_priority_song_1, response.context['new_songs'])
        self.assertNotIn(low_priority_song_2, response.context['new_songs'])
        self.assertNotIn(claimed_high_priority_song, response.context['new_songs'])
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
        claimed_song = song_factories.NewSongFactory(uploader_profile=None, claimed_by=user.profile)

        response = self.client.get(f"{reverse('screening_index')}?filter=low_priority")

        # Assert
        self.assertIn(low_priority_song_1, response.context['new_songs'])
        self.assertIn(low_priority_song_2, response.context['new_songs'])
        self.assertNotIn(high_priority_song_1, response.context['new_songs'])
        self.assertNotIn(high_priority_song_2, response.context['new_songs'])
        self.assertNotIn(claimed_song, response.context['new_songs'])
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
        song_that_should_be_excluded = song_factories.NewSongFactory(uploader_profile=uploading_user.profile, is_by_uploader=True, claimed_by=user.profile)

        response = self.client.get(f"{reverse('screening_index')}?filter=by_uploader")

        # Assert
        self.assertIn(high_priority_song_2, response.context['new_songs'])
        self.assertNotIn(song_that_should_be_excluded, response.context['new_songs'])
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
        song_that_should_be_excluded = song_factories.NewSongFactory(uploader_profile=uploading_user.profile, claimed_by=user.profile)

        response = self.client.get(f"{reverse('screening_index')}")

        # Assert
        self.assertIn(high_priority_song_1, response.context['new_songs'])
        self.assertIn(high_priority_song_2, response.context['new_songs'])
        self.assertIn(low_priority_song_1, response.context['new_songs'])
        self.assertIn(low_priority_song_2, response.context['new_songs'])
        self.assertNotIn(song_that_should_be_excluded, response.context['new_songs'])
        self.assertEqual(len(response.context['new_songs']), 4)

    def test_screening_view_shows_songs_claimed_by_current_user(self):
        uploading_user = factories.UserFactory()
        user = factories.UserFactory()
        permission = Permission.objects.get(codename='can_approve_songs')
        user.user_permissions.add(permission)
        self.client.force_login(user)

        song_factories.NewSongFactory(uploader_profile=uploading_user.profile)
        song_factories.NewSongFactory(uploader_profile=uploading_user.profile)
        song_factories.NewSongFactory(uploader_profile=None)
        song_factories.NewSongFactory(uploader_profile=None)
        user_screening_song = song_factories.NewSongFactory(uploader_profile=None, claimed_by=user.profile)

        response = self.client.get(f"{reverse('screening_index')}?filter=my_screening")

        # Assert
        self.assertEqual(len(response.context['new_songs']), 1)
        self.assertIn(user_screening_song, response.context['new_songs'])

    def test_screening_view_shows_songs_claimed_by_others(self):
        uploading_user = factories.UserFactory()
        user = factories.UserFactory()
        other_user = factories.UserFactory()
        permission = Permission.objects.get(codename='can_approve_songs')
        user.user_permissions.add(permission)
        self.client.force_login(user)

        song_factories.NewSongFactory(uploader_profile=uploading_user.profile)
        song_factories.NewSongFactory(uploader_profile=uploading_user.profile)
        song_factories.NewSongFactory(uploader_profile=None)
        song_factories.NewSongFactory(uploader_profile=None)
        user_screening_song = song_factories.NewSongFactory(uploader_profile=None, claimed_by=other_user.profile)

        response = self.client.get(f"{reverse('screening_index')}?filter=others_screening")

        # Assert
        self.assertEqual(len(response.context['new_songs']), 1)
        self.assertIn(user_screening_song, response.context['new_songs'])

    def test_claimed_songs_are_released_if_no_action_taken(self):
        uploading_user = factories.UserFactory()
        user = factories.UserFactory()
        other_user = factories.UserFactory()
        permission = Permission.objects.get(codename='can_approve_songs')
        user.user_permissions.add(permission)
        self.client.force_login(user)

        # Claimed more than 48 hours ago
        song_factories.NewSongFactory(uploader_profile=uploading_user.profile, claimed_by=other_user.profile, claim_date=timezone.now() - timedelta(hours=49))
        song_factories.NewSongFactory(uploader_profile=uploading_user.profile)
        song_factories.NewSongFactory(uploader_profile=None)
        song_factories.NewSongFactory(uploader_profile=None)
        user_screening_song = song_factories.NewSongFactory(uploader_profile=None, claimed_by=other_user.profile, claim_date=timezone.now())

        response = self.client.get(f"{reverse('screening_index')}?filter=others_screening")

        # Assert
        self.assertEqual(len(response.context['new_songs']), 1)
        self.assertIn(user_screening_song, response.context['new_songs'])

    def test_screening_view_shows_prescreened_songs(self):
        uploading_user = factories.UserFactory()
        user = factories.UserFactory()
        permission = Permission.objects.get(codename='can_approve_songs')
        user.user_permissions.add(permission)
        self.client.force_login(user)

        pre_screened_song_1 = song_factories.NewSongFactory(uploader_profile=uploading_user.profile, flag=NewSong.Flags.PRE_SCREENED)
        song_factories.NewSongFactory(uploader_profile=uploading_user.profile)
        song_factories.NewSongFactory(uploader_profile=None)
        song_factories.NewSongFactory(uploader_profile=None)
        pre_screened_song_2 = song_factories.NewSongFactory(uploader_profile=None, flag=NewSong.Flags.PRE_SCREENED)

        response = self.client.get(f"{reverse('screening_index')}?filter=pre_screened")

        # Assert
        self.assertEqual(len(response.context['new_songs']), 2)
        self.assertIn(pre_screened_song_1, response.context['new_songs'])
        self.assertIn(pre_screened_song_2, response.context['new_songs'])

    def test_screening_view_shows_prescreened_and_recommended_songs(self):
        uploading_user = factories.UserFactory()
        user = factories.UserFactory()
        permission = Permission.objects.get(codename='can_approve_songs')
        user.user_permissions.add(permission)
        self.client.force_login(user)

        pre_screened_song_1 = song_factories.NewSongFactory(uploader_profile=uploading_user.profile, flag=NewSong.Flags.PRE_SCREENED_PLUS)
        song_factories.NewSongFactory(uploader_profile=uploading_user.profile)
        song_factories.NewSongFactory(uploader_profile=None)
        song_factories.NewSongFactory(uploader_profile=None)
        pre_screened_song_2 = song_factories.NewSongFactory(uploader_profile=None, flag=NewSong.Flags.PRE_SCREENED_PLUS)

        response = self.client.get(f"{reverse('screening_index')}?filter=pre_screened_plus")

        # Assert
        self.assertEqual(len(response.context['new_songs']), 2)
        self.assertIn(pre_screened_song_1, response.context['new_songs'])
        self.assertIn(pre_screened_song_2, response.context['new_songs'])
