from django.test import TestCase
from django.urls.base import reverse
from django.contrib.auth.models import Permission

from songs import factories as song_factories
from uploads import factories as upload_factories
from uploads import constants
from uploads.models import NewSong
from homepage.tests import factories

class ScreenSongAuthenticationTests(TestCase):
    def test_unauthenticated_user_is_redirected_to_login(self):
        # Arrange
        song = upload_factories.NewSongFactory()
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
        song = upload_factories.NewSongFactory()
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
        song = upload_factories.NewSongFactory()
        self.client.force_login(user)

        # Act
        response = self.client.get(reverse('screen_song', kwargs = {'pk': song.id}))

        # Assert
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, "screen_song.html")
        self.assertIn('new_song', response.context)
        self.assertEqual(song, response.context['new_song'])

class ScreenSongContextDataTests(TestCase):
    def setUp(self):
        self.user = factories.UserFactory()
        self.permission = Permission.objects.get(codename='can_approve_songs')
        self.user.user_permissions.add(self.permission)
        self.client.force_login(self.user)

    def test_unclaimed_song_has_correct_context_data(self):
        # Arrange
        song = upload_factories.NewSongFactory()

        # Act
        response = self.client.get(reverse('screen_song', kwargs = {'pk': song.id}))

        # Assert
        self.assertIn('claimed_by_me', response.context)
        self.assertFalse(response.context['claimed_by_me'])
        self.assertIn('claimed_by_other_user', response.context)
        self.assertFalse(response.context['claimed_by_other_user'])
        self.assertEqual(1, len(response.context['actions']))
        self.assertIn(constants.CLAIM_ACTION, response.context['actions'])

    def test_claimed_song_with_no_flags_has_correct_context_data(self):
        # Arrange
        song = upload_factories.NewSongFactory(claimed_by=self.user.profile)

        # Act
        response = self.client.get(reverse('screen_song', kwargs = {'pk': song.id}))

        # Assert
        self.assertIn('claimed_by_me', response.context)
        self.assertTrue(response.context['claimed_by_me'])
        self.assertEqual(10, len(response.context['actions']))
        self.assertIn(constants.PRE_SCREEN_ACTION, response.context['actions'])
        self.assertIn(constants.PRE_SCREEN_AND_RECOMMEND_ACTION, response.context['actions'])
        self.assertIn(constants.NEEDS_SECOND_OPINION_ACTION, response.context['actions'])
        self.assertIn(constants.POSSIBLE_DUPLICATE_ACTION, response.context['actions'])
        self.assertIn(constants.UNDER_INVESTIGATION_ACTION, response.context['actions'])
        self.assertIn(constants.APPROVE_ACTION, response.context['actions'])
        self.assertIn(constants.APPROVE_AND_FEATURE_ACTION, response.context['actions'])
        self.assertIn(constants.UNCLAIM_ACTION, response.context['actions'])
        self.assertIn(constants.REJECT_ACTION, response.context['actions'])
        self.assertIn(constants.RENAME_ACTION, response.context['actions'])

    def test_song_claimed_by_other_has_correct_context_data(self):
        # Arrange
        other_user = factories.UserFactory()
        song = upload_factories.NewSongFactory(claimed_by=other_user.profile)

        # Act
        response = self.client.get(reverse('screen_song', kwargs = {'pk': song.id}))

        # Assert
        self.assertEqual(0, len(response.context['actions']))
        self.assertIn('claimed_by_me', response.context)
        self.assertFalse(response.context['claimed_by_me'])
        self.assertIn('claimed_by_other_user', response.context)
        self.assertTrue(response.context['claimed_by_other_user'])

    def test_claimed_song_and_flagged_by_self_as_second_opinion_has_correct_context_data(self):
        # Arrange
        song = upload_factories.NewSongFactory(claimed_by=self.user.profile, flagged_by=self.user.profile, flag=NewSong.Flags.NEEDS_SECOND_OPINION)

        # Act
        response = self.client.get(reverse('screen_song', kwargs={'pk': song.id}))

        # Assert
        self.assertIn('flag_message', response.context)
        self.assertEqual(response.context['flag_message'], constants.FLAG_MESSAGE_SECOND_OPINION)
        self.assertIn('flag_message_class', response.context)
        self.assertEqual(response.context['flag_message_class'], 'warning')
        self.assertEqual(3, len(response.context['actions']))
        self.assertIn(constants.UNCLAIM_ACTION, response.context['actions'])
        self.assertIn(constants.CLEAR_FLAG_ACTION, response.context['actions'])
        self.assertIn(constants.RENAME_ACTION, response.context['actions'])

    def test_claimed_song_needing_second_opinion_has_correct_context_data(self):
        # Arrange
        song = upload_factories.NewSongFactory(claimed_by=self.user.profile, flag=NewSong.Flags.NEEDS_SECOND_OPINION)

        # Act
        response = self.client.get(reverse('screen_song', kwargs={'pk': song.id}))

        # Assert
        self.assertIn('flag_message', response.context)
        self.assertEqual(response.context['flag_message'], constants.FLAG_MESSAGE_SECOND_OPINION)
        self.assertIn('flag_message_class', response.context)
        self.assertEqual(response.context['flag_message_class'], 'warning')
        self.assertEqual(10, len(response.context['actions']))
        self.assertIn(constants.PRE_SCREEN_ACTION, response.context['actions'])
        self.assertIn(constants.PRE_SCREEN_AND_RECOMMEND_ACTION, response.context['actions'])
        self.assertIn(constants.POSSIBLE_DUPLICATE_ACTION, response.context['actions'])
        self.assertIn(constants.UNDER_INVESTIGATION_ACTION, response.context['actions'])
        self.assertIn(constants.APPROVE_ACTION, response.context['actions'])
        self.assertIn(constants.APPROVE_AND_FEATURE_ACTION, response.context['actions'])
        self.assertIn(constants.UNCLAIM_ACTION, response.context['actions'])
        self.assertIn(constants.REJECT_ACTION, response.context['actions'])
        self.assertIn(constants.CLEAR_FLAG_ACTION, response.context['actions'])
        self.assertIn(constants.RENAME_ACTION, response.context['actions'])

    def test_claimed_song_possible_duplicate_has_correct_context_data(self):
        # Arrange
        song = upload_factories.NewSongFactory(claimed_by=self.user.profile, flag=NewSong.Flags.POSSIBLE_DUPLICATE)

        # Act
        response = self.client.get(reverse('screen_song', kwargs={'pk': song.id}))

        # Assert
        self.assertIn('flag_message', response.context)
        self.assertEqual(response.context['flag_message'], constants.FLAG_MESSAGE_POSSIBLE_DUPLICATE)
        self.assertIn('flag_message_class', response.context)
        self.assertEqual(response.context['flag_message_class'], 'warning')
        self.assertEqual(8, len(response.context['actions']))
        self.assertIn(constants.PRE_SCREEN_ACTION, response.context['actions'])
        self.assertIn(constants.PRE_SCREEN_AND_RECOMMEND_ACTION, response.context['actions'])
        self.assertIn(constants.NEEDS_SECOND_OPINION_ACTION, response.context['actions'])
        self.assertIn(constants.UNDER_INVESTIGATION_ACTION, response.context['actions'])
        self.assertIn(constants.UNCLAIM_ACTION, response.context['actions'])
        self.assertIn(constants.REJECT_ACTION, response.context['actions'])
        self.assertIn(constants.CLEAR_FLAG_ACTION, response.context['actions'])
        self.assertIn(constants.RENAME_ACTION, response.context['actions'])

    def test_song_under_investigation_has_correct_context_data(self):
        # Arrange
        song = upload_factories.NewSongFactory(claimed_by=self.user.profile, flag=NewSong.Flags.UNDER_INVESTIGATION)

        # Act
        response = self.client.get(reverse('screen_song', kwargs={'pk': song.id}))

        # Assert
        self.assertIn('flag_message', response.context)
        self.assertEqual(response.context['flag_message'], constants.FLAG_MESSAGE_UNDER_INVESTIGATION)
        self.assertIn('flag_message_class', response.context)
        self.assertEqual(response.context['flag_message_class'], 'warning')
        self.assertEqual(8, len(response.context['actions']))
        self.assertIn(constants.PRE_SCREEN_ACTION, response.context['actions'])
        self.assertIn(constants.PRE_SCREEN_AND_RECOMMEND_ACTION, response.context['actions'])
        self.assertIn(constants.NEEDS_SECOND_OPINION_ACTION, response.context['actions'])
        self.assertIn(constants.POSSIBLE_DUPLICATE_ACTION, response.context['actions'])
        self.assertIn(constants.UNCLAIM_ACTION, response.context['actions'])
        self.assertIn(constants.REJECT_ACTION, response.context['actions'])
        self.assertIn(constants.CLEAR_FLAG_ACTION, response.context['actions'])
        self.assertIn(constants.RENAME_ACTION, response.context['actions'])

    def test_claimed_pre_screened_song_has_correct_context_data(self):
        # Arrange
        song = upload_factories.NewSongFactory(claimed_by=self.user.profile, flag=NewSong.Flags.PRE_SCREENED)

        # Act
        response = self.client.get(reverse('screen_song', kwargs={'pk': song.id}))

        # Assert
        self.assertIn('flag_message', response.context)
        self.assertEqual(response.context['flag_message'], constants.FLAG_MESSAGE_PRE_SCREENED)
        self.assertIn('flag_message_class', response.context)
        self.assertEqual(response.context['flag_message_class'], 'success')
        self.assertEqual(6, len(response.context['actions']))
        self.assertIn(constants.APPROVE_ACTION, response.context['actions'])
        self.assertIn(constants.APPROVE_AND_FEATURE_ACTION, response.context['actions'])
        self.assertIn(constants.UNCLAIM_ACTION, response.context['actions'])
        self.assertIn(constants.REJECT_ACTION, response.context['actions'])
        self.assertIn(constants.CLEAR_FLAG_ACTION, response.context['actions'])
        self.assertIn(constants.RENAME_ACTION, response.context['actions'])

    def test_claimed_pre_screened_and_recommended_song_has_correct_context_data(self):
        # Arrange
        song = upload_factories.NewSongFactory(claimed_by=self.user.profile, flag=NewSong.Flags.PRE_SCREENED_PLUS)

        # Act
        response = self.client.get(reverse('screen_song', kwargs={'pk': song.id}))

        # Assert
        self.assertIn('flag_message', response.context)
        self.assertEqual(response.context['flag_message'], constants.FLAG_MESSAGE_PRE_SCREENED_AND_RECOMMENDED)
        self.assertIn('flag_message_class', response.context)
        self.assertEqual(response.context['flag_message_class'], 'success')
        self.assertEqual(6, len(response.context['actions']))
        self.assertIn(constants.APPROVE_ACTION, response.context['actions'])
        self.assertIn(constants.APPROVE_AND_FEATURE_ACTION, response.context['actions'])
        self.assertIn(constants.UNCLAIM_ACTION, response.context['actions'])
        self.assertIn(constants.REJECT_ACTION, response.context['actions'])
        self.assertIn(constants.CLEAR_FLAG_ACTION, response.context['actions'])
        self.assertIn(constants.RENAME_ACTION, response.context['actions'])
