from datetime import timedelta
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls.base import reverse
from django.utils import timezone

from homepage.tests import factories
from songs import factories as song_factories
from songs.models import NewSong
from songs import constants

class ScreeningIndexAuthTests(TestCase):
    def test_screening_view_permits_access_to_authenticated_users(self):
        user = factories.UserFactory()
        permission = Permission.objects.get(codename='can_approve_songs')
        user.user_permissions.add(permission)
        self.client.force_login(user)

        response = self.client.get(reverse('screening_index'))

        # Assert
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, "screening_index.html")

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

class ScreeningIndexAvailableActionTests(TestCase):
    def setUp(self):
        self.user = factories.UserFactory()
        permission = Permission.objects.get(codename='can_approve_songs')
        self.user.user_permissions.add(permission)
        self.client.force_login(self.user)

    def test_high_priority_filter_only_shows_claim_action(self):
        # Act
        response = self.client.get(f"{reverse('screening_index')}?filter={constants.HIGH_PRIORITY_FILTER}")

        # Assert
        self.assertEqual(len(response.context['actions']), 1)
        self.assertIn(constants.CLAIM_ACTION, response.context['actions'])

    def test_low_priority_filter_only_shows_claim_action(self):
        # Act
        response = self.client.get(f"{reverse('screening_index')}?filter={constants.LOW_PRIORITY_FILTER}")

        # Assert
        self.assertEqual(len(response.context['actions']), 1)
        self.assertIn(constants.CLAIM_ACTION, response.context['actions'])

    def test_by_uploader_filter_only_shows_claim_action(self):
        # Act
        response = self.client.get(f"{reverse('screening_index')}?filter={constants.BY_UPLOADER_FILTER}")

        # Assert
        self.assertEqual(len(response.context['actions']), 1)
        self.assertIn(constants.CLAIM_ACTION, response.context['actions'])

    def test_my_screening_filter_shows_legal_actions(self):
        # Act
        response = self.client.get(f"{reverse('screening_index')}?filter={constants.MY_SCREENING_FILTER}")

        # Assert
        self.assertEqual(len(response.context['actions']), 6)
        self.assertIn(constants.PRE_SCREEN_ACTION, response.context['actions'])
        self.assertIn(constants.PRE_SCREEN_AND_RECOMMEND_ACTION, response.context['actions'])
        self.assertIn(constants.NEEDS_SECOND_OPINION_ACTION, response.context['actions'])
        self.assertIn(constants.POSSIBLE_DUPLICATE_ACTION, response.context['actions'])
        self.assertIn(constants.UNDER_INVESTIGATION_ACTION, response.context['actions'])
        self.assertIn(constants.UNCLAIM_ACTION, response.context['actions'])

    def test_others_screening_filter_contains_no_actions(self):
        # Act
        response = self.client.get(f"{reverse('screening_index')}?filter={constants.OTHERS_SCREENING_FILTER}")

        # Assert
        self.assertEqual(len(response.context['actions']), 0)

    def test_prescreened_filter_shows_legal_actions(self):
        # Act
        response = self.client.get(f"{reverse('screening_index')}?filter={constants.PRE_SCREENED_FILTER}")

        # Assert
        self.assertEqual(len(response.context['actions']), 2)
        self.assertIn(constants.APPROVE_ACTION, response.context['actions'])
        self.assertIn(constants.APPROVE_AND_FEATURE_ACTION, response.context['actions'])

    def test_prescreened_and_recommended_filter_shows_legal_actions(self):
        # Act
        response = self.client.get(f"{reverse('screening_index')}?filter={constants.PRE_SCREENED_AND_RECOMMENDED_FILTER}")

        # Assert
        self.assertEqual(len(response.context['actions']), 2)
        self.assertIn(constants.APPROVE_ACTION, response.context['actions'])
        self.assertIn(constants.APPROVE_AND_FEATURE_ACTION, response.context['actions'])

class ScreeningIndexFilteringTests(TestCase):
    def setUp(self):
        self.user = factories.UserFactory()
        permission = Permission.objects.get(codename='can_approve_songs')
        self.user.user_permissions.add(permission)
        self.client.force_login(self.user)

    def test_screening_view_contains_new_songs(self):
        song = song_factories.NewSongFactory(filename='song1.mod', uploader_profile=self.user.profile)

        response = self.client.get(reverse('screening_index'))

        # Assert
        self.assertIn(song, response.context['new_songs'])
        self.assertEqual(len(response.context['new_songs']), 1)

    def test_screening_view_filters_high_priority_songs(self):
        uploading_user = factories.UserFactory()

        high_priority_song_1 = song_factories.NewSongFactory(uploader_profile=uploading_user.profile)
        high_priority_song_2 = song_factories.NewSongFactory(uploader_profile=uploading_user.profile)
        low_priority_song_1 = song_factories.NewSongFactory(uploader_profile=None)
        low_priority_song_2 = song_factories.NewSongFactory(uploader_profile=None)
        claimed_high_priority_song = song_factories.NewSongFactory(uploader_profile=uploading_user.profile, claimed_by=self.user.profile)

        response = self.client.get(f"{reverse('screening_index')}?filter={constants.HIGH_PRIORITY_FILTER}")

        # Assert
        self.assertIn(high_priority_song_1, response.context['new_songs'])
        self.assertIn(high_priority_song_2, response.context['new_songs'])
        self.assertNotIn(low_priority_song_1, response.context['new_songs'])
        self.assertNotIn(low_priority_song_2, response.context['new_songs'])
        self.assertNotIn(claimed_high_priority_song, response.context['new_songs'])
        self.assertEqual(len(response.context['new_songs']), 2)

    def test_screening_view_filters_low_priority_songs(self):
        uploading_user = factories.UserFactory()

        high_priority_song_1 = song_factories.NewSongFactory(uploader_profile=uploading_user.profile)
        high_priority_song_2 = song_factories.NewSongFactory(uploader_profile=uploading_user.profile)
        low_priority_song_1 = song_factories.NewSongFactory(uploader_profile=None)
        low_priority_song_2 = song_factories.NewSongFactory(uploader_profile=None)
        claimed_song = song_factories.NewSongFactory(uploader_profile=None, claimed_by=self.user.profile)

        response = self.client.get(f"{reverse('screening_index')}?filter={constants.LOW_PRIORITY_FILTER}")

        # Assert
        self.assertIn(low_priority_song_1, response.context['new_songs'])
        self.assertIn(low_priority_song_2, response.context['new_songs'])
        self.assertNotIn(high_priority_song_1, response.context['new_songs'])
        self.assertNotIn(high_priority_song_2, response.context['new_songs'])
        self.assertNotIn(claimed_song, response.context['new_songs'])
        self.assertEqual(len(response.context['new_songs']), 2)

    def test_screening_view_filters_songs_by_uploader(self):
        uploading_user = factories.UserFactory()

        song_factories.NewSongFactory(uploader_profile=uploading_user.profile)
        high_priority_song_2 = song_factories.NewSongFactory(uploader_profile=uploading_user.profile, is_by_uploader=True)
        song_factories.NewSongFactory(uploader_profile=None)
        song_factories.NewSongFactory(uploader_profile=None)
        song_that_should_be_excluded = song_factories.NewSongFactory(uploader_profile=uploading_user.profile, is_by_uploader=True, claimed_by=self.user.profile)

        response = self.client.get(f"{reverse('screening_index')}?filter={constants.BY_UPLOADER_FILTER}")

        # Assert
        self.assertIn(high_priority_song_2, response.context['new_songs'])
        self.assertNotIn(song_that_should_be_excluded, response.context['new_songs'])
        self.assertEqual(len(response.context['new_songs']), 1)

    def test_screening_view_shows_high_priority_songs_by_default(self):
        uploading_user = factories.UserFactory()

        high_priority_song_1 = song_factories.NewSongFactory(uploader_profile=uploading_user.profile)
        high_priority_song_2 = song_factories.NewSongFactory(uploader_profile=uploading_user.profile)
        low_priority_song_1 = song_factories.NewSongFactory(uploader_profile=None)
        low_priority_song_2 = song_factories.NewSongFactory(uploader_profile=None)
        song_that_should_be_excluded = song_factories.NewSongFactory(uploader_profile=uploading_user.profile, claimed_by=self.user.profile)

        response = self.client.get(f"{reverse('screening_index')}")

        # Assert
        self.assertIn(high_priority_song_1, response.context['new_songs'])
        self.assertIn(high_priority_song_2, response.context['new_songs'])
        self.assertNotIn(low_priority_song_1, response.context['new_songs'])
        self.assertNotIn(low_priority_song_2, response.context['new_songs'])
        self.assertNotIn(song_that_should_be_excluded, response.context['new_songs'])
        self.assertEqual(len(response.context['new_songs']), 2)

    def test_screening_view_shows_songs_claimed_by_current_user(self):
        uploading_user = factories.UserFactory()

        song_factories.NewSongFactory(uploader_profile=uploading_user.profile)
        song_factories.NewSongFactory(uploader_profile=uploading_user.profile)
        song_factories.NewSongFactory(uploader_profile=None)
        song_factories.NewSongFactory(uploader_profile=None)
        user_screening_song = song_factories.NewSongFactory(uploader_profile=None, claimed_by=self.user.profile)

        response = self.client.get(f"{reverse('screening_index')}?filter={constants.MY_SCREENING_FILTER}")

        # Assert
        self.assertEqual(len(response.context['new_songs']), 1)
        self.assertIn(user_screening_song, response.context['new_songs'])

    def test_screening_view_shows_songs_claimed_by_others(self):
        uploading_user = factories.UserFactory()
        other_user = factories.UserFactory()

        song_factories.NewSongFactory(uploader_profile=uploading_user.profile)
        song_factories.NewSongFactory(uploader_profile=uploading_user.profile)
        song_factories.NewSongFactory(uploader_profile=None)
        song_factories.NewSongFactory(uploader_profile=None)
        user_screening_song = song_factories.NewSongFactory(uploader_profile=None, claimed_by=other_user.profile)

        response = self.client.get(f"{reverse('screening_index')}?filter={constants.OTHERS_SCREENING_FILTER}")

        # Assert
        self.assertEqual(len(response.context['new_songs']), 1)
        self.assertIn(user_screening_song, response.context['new_songs'])

    def test_claimed_songs_are_released_if_no_action_taken(self):
        uploading_user = factories.UserFactory()
        other_user = factories.UserFactory()

        # Claimed more than 48 hours ago
        song_factories.NewSongFactory(uploader_profile=uploading_user.profile, claimed_by=other_user.profile, claim_date=timezone.now() - timedelta(hours=49))
        song_factories.NewSongFactory(uploader_profile=uploading_user.profile)
        song_factories.NewSongFactory(uploader_profile=None)
        song_factories.NewSongFactory(uploader_profile=None)
        user_screening_song = song_factories.NewSongFactory(uploader_profile=None, claimed_by=other_user.profile, claim_date=timezone.now())

        response = self.client.get(f"{reverse('screening_index')}?filter={constants.OTHERS_SCREENING_FILTER}")

        # Assert
        self.assertEqual(len(response.context['new_songs']), 1)
        self.assertIn(user_screening_song, response.context['new_songs'])

    def test_screening_view_shows_prescreened_songs(self):
        uploading_user = factories.UserFactory()

        pre_screened_song_1 = song_factories.NewSongFactory(uploader_profile=uploading_user.profile, flag=NewSong.Flags.PRE_SCREENED)
        song_factories.NewSongFactory(uploader_profile=uploading_user.profile)
        song_factories.NewSongFactory(uploader_profile=None)
        song_factories.NewSongFactory(uploader_profile=None)
        pre_screened_song_2 = song_factories.NewSongFactory(uploader_profile=None, flag=NewSong.Flags.PRE_SCREENED)

        response = self.client.get(f"{reverse('screening_index')}?filter={constants.PRE_SCREENED_FILTER}")

        # Assert
        self.assertEqual(len(response.context['new_songs']), 2)
        self.assertIn(pre_screened_song_1, response.context['new_songs'])
        self.assertIn(pre_screened_song_2, response.context['new_songs'])

    def test_screening_view_shows_prescreened_and_recommended_songs(self):
        uploading_user = factories.UserFactory()

        pre_screened_song_1 = song_factories.NewSongFactory(uploader_profile=uploading_user.profile, flag=NewSong.Flags.PRE_SCREENED_PLUS)
        song_factories.NewSongFactory(uploader_profile=uploading_user.profile)
        song_factories.NewSongFactory(uploader_profile=None)
        song_factories.NewSongFactory(uploader_profile=None)
        pre_screened_song_2 = song_factories.NewSongFactory(uploader_profile=None, flag=NewSong.Flags.PRE_SCREENED_PLUS)

        response = self.client.get(f"{reverse('screening_index')}?filter={constants.PRE_SCREENED_AND_RECOMMENDED_FILTER}")

        # Assert
        self.assertEqual(len(response.context['new_songs']), 2)
        self.assertIn(pre_screened_song_1, response.context['new_songs'])
        self.assertIn(pre_screened_song_2, response.context['new_songs'])

    def test_high_priority_filter_does_not_show_prescreened_songs(self):
        # Arrange
        song_factories.NewSongFactory(uploader_profile=self.user.profile, flag=NewSong.Flags.PRE_SCREENED)
        song_factories.NewSongFactory(uploader_profile=self.user.profile, flag=NewSong.Flags.PRE_SCREENED_PLUS)
        high_priority_song_1 = song_factories.NewSongFactory(uploader_profile=self.user.profile)

        # Act
        response = self.client.get(f"{reverse('screening_index')}?filter={constants.HIGH_PRIORITY_FILTER}")

        # Assert
        self.assertEqual(len(response.context['new_songs']), 1)
        self.assertIn(high_priority_song_1, response.context['new_songs'])

    def test_low_priority_filter_does_not_show_prescreened_songs(self):
        # Arrange
        song_factories.NewSongFactory(flag=NewSong.Flags.PRE_SCREENED)
        song_factories.NewSongFactory(flag=NewSong.Flags.PRE_SCREENED_PLUS)
        low_priority_song_1 = song_factories.NewSongFactory()

        # Act
        response = self.client.get(f"{reverse('screening_index')}?filter={constants.LOW_PRIORITY_FILTER}")

        # Assert
        self.assertEqual(len(response.context['new_songs']), 1)
        self.assertIn(low_priority_song_1, response.context['new_songs'])

    def test_uploaded_by_artist_filter_does_not_show_prescreened_songs(self):
        # Arrange
        song_factories.NewSongFactory(flag=NewSong.Flags.PRE_SCREENED, is_by_uploader=True)
        song_factories.NewSongFactory(flag=NewSong.Flags.PRE_SCREENED_PLUS, is_by_uploader=True)
        by_uploader_song_1 = song_factories.NewSongFactory(is_by_uploader=True)

        # Act
        response = self.client.get(f"{reverse('screening_index')}?filter={constants.BY_UPLOADER_FILTER}")

        # Assert
        self.assertEqual(len(response.context['new_songs']), 1)
        self.assertIn(by_uploader_song_1, response.context['new_songs'])

    def test_second_opinion_filter_only_shows_songs_with_second_opinion_flag(self):
        # Arrange
        song_factories.NewSongFactory(flag=NewSong.Flags.PRE_SCREENED)
        song_factories.NewSongFactory(flag=NewSong.Flags.PRE_SCREENED_PLUS)
        second_opinion_song_1 = song_factories.NewSongFactory(flag=NewSong.Flags.NEEDS_SECOND_OPINION)
        second_opinion_song_2 = song_factories.NewSongFactory(flag=NewSong.Flags.NEEDS_SECOND_OPINION)

        # Act
        response = self.client.get(f"{reverse('screening_index')}?filter={constants.NEEDS_SECOND_OPINION_FILTER}")

        # Assert
        self.assertEqual(len(response.context['new_songs']), 2)
        self.assertIn(second_opinion_song_1, response.context['new_songs'])
        self.assertIn(second_opinion_song_2, response.context['new_songs'])

    def test_possible_duplicate_filter_only_shows_songs_with_possible_duplicate_flag(self):
        # Arrange
        song_factories.NewSongFactory(flag=NewSong.Flags.PRE_SCREENED)
        song_factories.NewSongFactory(flag=NewSong.Flags.PRE_SCREENED_PLUS)
        possible_duplicate_song_1 = song_factories.NewSongFactory(flag=NewSong.Flags.POSSIBLE_DUPLICATE)
        possible_duplicate_song_2 = song_factories.NewSongFactory(flag=NewSong.Flags.POSSIBLE_DUPLICATE)

        # Act
        response = self.client.get(f"{reverse('screening_index')}?filter={constants.POSSIBLE_DUPLICATE_FILTER}")

        # Assert
        self.assertEqual(len(response.context['new_songs']), 2)
        self.assertIn(possible_duplicate_song_1, response.context['new_songs'])
        self.assertIn(possible_duplicate_song_2, response.context['new_songs'])

    def test_under_investigation_filter_only_shows_songs_with_under_investigation_flag(self):
        # Arrange
        song_factories.NewSongFactory(flag=NewSong.Flags.PRE_SCREENED)
        song_factories.NewSongFactory(flag=NewSong.Flags.PRE_SCREENED_PLUS)
        under_investigation_song_1 = song_factories.NewSongFactory(flag=NewSong.Flags.UNDER_INVESTIGATION)
        under_investigation_song_2 = song_factories.NewSongFactory(flag=NewSong.Flags.UNDER_INVESTIGATION)

        # Act
        response = self.client.get(f"{reverse('screening_index')}?filter={constants.UNDER_INVESTIGATION_FILTER}")

        # Assert
        self.assertEqual(len(response.context['new_songs']), 2)
        self.assertIn(under_investigation_song_1, response.context['new_songs'])
        self.assertIn(under_investigation_song_2, response.context['new_songs'])
