import os
import shutil

from django.conf import settings
from django.contrib.auth.models import Permission
from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls.base import reverse

from artists.factories import ArtistFactory
from homepage.tests import factories
from songs import factories as song_factories
from songs.models import Song
from uploads import constants
from uploads import factories as upload_factories
from uploads.models import NewSong, ScreeningEvent

SONG_1_FILENAME = 'song1.mod'
SONG_2_FILENAME = 'song2.mod'
SONG_3_FILENAME = 'my_song.it'

class ScreeningActionViewAuthenticationTests(TestCase):
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
        self.assertRedirects(response, reverse('screening_index'))

class ClaimingActionTests(TestCase):
    my_screening_index = f'{reverse("screening_index")}?filter={constants.MY_SCREENING_FILTER}'

    def setUp(self):
        self.user = factories.UserFactory()
        self.permission = Permission.objects.get(codename='can_approve_songs')
        self.user.user_permissions.add(self.permission)
        self.client.force_login(self.user)

    def test_screener_can_claim_single_unclaimed_song(self):
        # Arrange
        song1 = upload_factories.NewSongFactory(filename=SONG_1_FILENAME)

        # Act
        response = self.client.post(reverse('screening_action'), {'selected_songs': [song1.id], 'action': constants.CLAIM_KEYWORD})

        # Assert
        self.assertRedirects(response, self.my_screening_index)
        song1.refresh_from_db()
        self.assertEqual(self.user.profile, song1.claimed_by)
        self.assertIsNotNone(song1.claim_date)

        events = ScreeningEvent.objects.filter(new_song=song1)
        self.assertEqual(events.count(), 1)
        event = events.first()
        self.assertEqual(event.profile, self.user.profile)
        self.assertEqual(event.type, ScreeningEvent.Types.CLAIM)
        self.assertEqual(f'Claimed by {self.user.profile.display_name}', event.content)

    def test_screener_can_claim_multiple_unclaimed_songs(self):
        # Arrange
        song1 = upload_factories.NewSongFactory(filename=SONG_1_FILENAME)
        song2 = upload_factories.NewSongFactory(filename=SONG_2_FILENAME)

        # Act
        response = self.client.post(reverse('screening_action'), {'selected_songs': [song1.id, song2.id], 'action': constants.CLAIM_KEYWORD})

        # Assert
        self.assertRedirects(response, self.my_screening_index)
        song1.refresh_from_db()
        song2.refresh_from_db()
        self.assertEqual(self.user.profile, song1.claimed_by)
        self.assertIsNotNone(song1.claim_date)
        self.assertEqual(self.user.profile, song2.claimed_by)
        self.assertIsNotNone(song2.claim_date)

        events = ScreeningEvent.objects.filter(new_song=song1)
        self.assertEqual(events.count(), 1)
        event = events.first()
        self.assertEqual(event.profile, self.user.profile)
        self.assertEqual(event.type, ScreeningEvent.Types.CLAIM)
        self.assertEqual(f'Claimed by {self.user.profile.display_name}', event.content)

        events = ScreeningEvent.objects.filter(new_song=song2)
        self.assertEqual(events.count(), 1)
        event = events.first()
        self.assertEqual(event.profile, self.user.profile)
        self.assertEqual(event.type, ScreeningEvent.Types.CLAIM)
        self.assertEqual(f'Claimed by {self.user.profile.display_name}', event.content)

    def test_cannot_claim_songs_already_claimed_by_others(self):
        # Arrange
        other_user = factories.UserFactory()
        song1 = upload_factories.NewSongFactory(filename=SONG_1_FILENAME, claimed_by=other_user.profile)
        song2 = upload_factories.NewSongFactory(filename=SONG_2_FILENAME, claimed_by=other_user.profile)

        # Act
        response = self.client.post(reverse('screening_action'), {'selected_songs': [song1.id, song2.id], 'action': constants.CLAIM_KEYWORD})

        # Assert
        self.assertRedirects(response, reverse('screening_index'))
        song1.refresh_from_db()
        song2.refresh_from_db()
        self.assertEqual(other_user.profile, song1.claimed_by)
        self.assertEqual(other_user.profile, song2.claimed_by)

    def test_cannot_unclaim_song_claimed_by_others(self):
        # Arrange
        other_user = factories.UserFactory()
        song1 = upload_factories.NewSongFactory(claimed_by=other_user.profile)

        # Act
        response = self.client.post(reverse('screening_action'), {'selected_songs': [song1.id], 'action': constants.UNCLAIM_KEYWORD})

        # Assert
        self.assertRedirects(response, reverse('screening_index'))
        song1.refresh_from_db()
        self.assertEqual(other_user.profile, song1.claimed_by)

    def test_can_unclaim_song_if_claimed_by_user(self):
        # Arrange
        song1 = upload_factories.NewSongFactory(claimed_by=self.user.profile)

        # Act
        response = self.client.post(reverse('screening_action'), {'selected_songs': [song1.id], 'action': constants.UNCLAIM_KEYWORD})

        # Assert
        self.assertRedirects(response, reverse('screening_index'))
        song1.refresh_from_db()
        self.assertIsNone(song1.claimed_by)
        self.assertIsNone(song1.claim_date)

        events = ScreeningEvent.objects.filter(new_song=song1)
        self.assertEqual(events.count(), 1)
        event = events.first()
        self.assertEqual(event.profile, self.user.profile)
        self.assertEqual(event.type, ScreeningEvent.Types.UNCLAIM)
        self.assertEqual(f'Unclaimed by {self.user.profile.display_name}', event.content)

class FlaggingActionTests(TestCase):
    def setUp(self):
        self.user = factories.UserFactory()
        self.permission = Permission.objects.get(codename='can_approve_songs')
        self.user.user_permissions.add(self.permission)
        self.client.force_login(self.user)

    def test_can_flag_claimed_song_as_under_investigation(self):
        # Arrange
        song1 = upload_factories.NewSongFactory(claimed_by=self.user.profile)

        # Act
        response = self.client.post(reverse('screening_action'), {'selected_songs': [song1.id], 'action': constants.UNDER_INVESTIGATION_KEYWORD})

        # Assert
        self.assertRedirects(response, f'{reverse("screening_index")}?filter={constants.UNDER_INVESTIGATION_FILTER}')
        song1.refresh_from_db()
        self.assertEqual(NewSong.Flags.UNDER_INVESTIGATION, song1.flag)
        self.assertEqual(self.user.profile, song1.flagged_by)

        events = ScreeningEvent.objects.filter(new_song=song1)
        self.assertEqual(events.count(), 1)
        event = events.first()
        self.assertEqual(event.profile, self.user.profile)
        self.assertEqual(event.type, ScreeningEvent.Types.APPLY_FLAG)
        self.assertEqual(f'Flag set to {NewSong.Flags.UNDER_INVESTIGATION} by {self.user.profile.display_name} (was None)', event.content)

    def test_cannot_flag_unclaimed_song_as_under_investigation(self):
        # Arrange
        song1 = upload_factories.NewSongFactory()

        # Act
        self.client.force_login(self.user)
        response = self.client.post(reverse('screening_action'), {'selected_songs': [song1.id], 'action': constants.UNDER_INVESTIGATION_KEYWORD})

        # Assert
        self.assertRedirects(response, reverse('screening_index'))
        song1.refresh_from_db()
        self.assertIsNone(song1.flag)
        self.assertIsNone(song1.flagged_by)

    def test_cannot_flag_song_claimed_by_others_as_under_investigation(self):
        # Arrange
        other_user = factories.UserFactory()
        song1 = upload_factories.NewSongFactory(claimed_by=other_user.profile)

        # Act
        response = self.client.post(reverse('screening_action'), {'selected_songs': [song1.id], 'action': constants.UNDER_INVESTIGATION_KEYWORD})

        # Assert
        self.assertRedirects(response, reverse('screening_index'))
        song1.refresh_from_db()
        self.assertIsNone(song1.flag)
        self.assertIsNone(song1.flagged_by)

    def test_can_flag_claimed_song_as_possible_duplicate(self):
        # Arrange
        song1 = upload_factories.NewSongFactory(claimed_by=self.user.profile)
        song2 = upload_factories.NewSongFactory(claimed_by=self.user.profile)
        song3 = upload_factories.NewSongFactory(claimed_by=self.user.profile)

        # Act
        response = self.client.post(reverse('screening_action'), {'selected_songs': [song1.id], 'action': constants.POSSIBLE_DUPLICATE_KEYWORD})

        # Assert
        self.assertRedirects(response, f'{reverse("screening_index")}?filter={constants.POSSIBLE_DUPLICATE_FILTER}')
        song1.refresh_from_db()
        song2.refresh_from_db()
        song3.refresh_from_db()
        self.assertEqual(NewSong.Flags.POSSIBLE_DUPLICATE, song1.flag)
        self.assertEqual(self.user.profile, song1.flagged_by)
        self.assertIsNone(song2.flag)
        self.assertIsNone(song2.flagged_by)
        self.assertIsNone(song3.flag)
        self.assertIsNone(song3.flagged_by)

        events = ScreeningEvent.objects.filter(new_song=song1)
        self.assertEqual(events.count(), 1)
        event = events.first()
        self.assertEqual(event.profile, self.user.profile)
        self.assertEqual(event.type, ScreeningEvent.Types.APPLY_FLAG)
        self.assertEqual(f'Flag set to {NewSong.Flags.POSSIBLE_DUPLICATE} by {self.user.profile.display_name} (was None)', event.content)

        events = ScreeningEvent.objects.filter(new_song=song2)
        self.assertEqual(events.count(), 0)

        events = ScreeningEvent.objects.filter(new_song=song3)
        self.assertEqual(events.count(), 0)

    def test_cannot_flag_unclaimed_song_as_possible_duplicate(self):
        # Arrange
        song1 = upload_factories.NewSongFactory()

        # Act
        response = self.client.post(reverse('screening_action'), {'selected_songs': [song1.id], 'action': constants.POSSIBLE_DUPLICATE_KEYWORD})

        # Assert
        self.assertRedirects(response, reverse('screening_index'))
        song1.refresh_from_db()
        self.assertIsNone(song1.flag)
        self.assertIsNone(song1.flagged_by)

    def test_cannot_flag_song_claimed_by_others_as_possible_duplicate(self):
        # Arrange
        other_user = factories.UserFactory()
        song1 = upload_factories.NewSongFactory(claimed_by=other_user.profile)

        # Act
        response = self.client.post(reverse('screening_action'), {'selected_songs': [song1.id], 'action': constants.POSSIBLE_DUPLICATE_KEYWORD})

        # Assert
        self.assertRedirects(response, reverse('screening_index'))
        song1.refresh_from_db()
        self.assertIsNone(song1.flag)
        self.assertIsNone(song1.flagged_by)

    def test_can_prescreen_claimed_songs(self):
        # Arrange
        song1 = upload_factories.NewSongFactory(filename=SONG_1_FILENAME, claimed_by=self.user.profile)
        song2 = upload_factories.NewSongFactory(filename=SONG_2_FILENAME, claimed_by=self.user.profile)

        # Act
        response = self.client.post(reverse('screening_action'), {'selected_songs': [song1.id, song2.id], 'action': constants.PRE_SCREEN_KEYWORD})

        # Assert
        self.assertRedirects(response, f'{reverse("screening_index")}?filter={constants.PRE_SCREENED_FILTER}')
        song1.refresh_from_db()
        song2.refresh_from_db()
        self.assertIsNone(song1.claimed_by)
        self.assertIsNone(song2.claimed_by)
        self.assertIsNone(song1.claim_date)
        self.assertIsNone(song2.claim_date)
        self.assertEqual(NewSong.Flags.PRE_SCREENED, song1.flag)
        self.assertEqual(NewSong.Flags.PRE_SCREENED, song2.flag)
        self.assertEqual(self.user.profile, song1.flagged_by)
        self.assertEqual(self.user.profile, song2.flagged_by)

        events = ScreeningEvent.objects.filter(new_song=song1)
        self.assertEqual(events.count(), 1)
        event = events.first()
        self.assertEqual(event.profile, self.user.profile)
        self.assertEqual(event.type, ScreeningEvent.Types.APPLY_FLAG)
        self.assertEqual(f'Flag set to {NewSong.Flags.PRE_SCREENED} by {self.user.profile.display_name} (was None)', event.content)

        events = ScreeningEvent.objects.filter(new_song=song2)
        self.assertEqual(events.count(), 1)
        event = events.first()
        self.assertEqual(event.profile, self.user.profile)
        self.assertEqual(event.type, ScreeningEvent.Types.APPLY_FLAG)
        self.assertEqual(f'Flag set to {NewSong.Flags.PRE_SCREENED} by {self.user.profile.display_name} (was None)', event.content)

    def test_cannot_prescreen_unclaimed_songs(self):
        # Arrange
        song1 = upload_factories.NewSongFactory(filename=SONG_1_FILENAME)
        song2 = upload_factories.NewSongFactory(filename=SONG_2_FILENAME)

        # Act
        response = self.client.post(reverse('screening_action'), {'selected_songs': [song1.id, song2.id], 'action': constants.PRE_SCREEN_KEYWORD})

        # Assert
        self.assertRedirects(response, reverse('screening_index'))
        song1.refresh_from_db()
        song2.refresh_from_db()
        self.assertIsNone(song1.claimed_by)
        self.assertIsNone(song2.claimed_by)
        self.assertIsNone(song1.claim_date)
        self.assertIsNone(song2.claim_date)
        self.assertIsNone(song1.flag)
        self.assertIsNone(song2.flag)

    def test_cannot_prescreen_songs_claimed_by_others(self):
        # Arrange
        other_user = factories.UserFactory()
        song1 = upload_factories.NewSongFactory(filename=SONG_1_FILENAME, claimed_by=other_user.profile)
        song2 = upload_factories.NewSongFactory(filename=SONG_2_FILENAME, claimed_by=other_user.profile)

        # Act
        response = self.client.post(reverse('screening_action'), {'selected_songs': [song1.id, song2.id], 'action': constants.PRE_SCREEN_KEYWORD})

        # Assert
        self.assertRedirects(response, reverse('screening_index'))
        song1.refresh_from_db()
        song2.refresh_from_db()
        self.assertEqual(other_user.profile, song1.claimed_by)
        self.assertEqual(other_user.profile, song2.claimed_by)
        self.assertIsNone(song1.flag)
        self.assertIsNone(song2.flag)

    def test_can_prescreen_and_recommend_claimed_songs(self):
        # Arrange
        song1 = upload_factories.NewSongFactory(filename=SONG_1_FILENAME, claimed_by=self.user.profile)
        song2 = upload_factories.NewSongFactory(filename=SONG_2_FILENAME, claimed_by=self.user.profile)

        # Act
        response = self.client.post(reverse('screening_action'), {'selected_songs': [song1.id, song2.id], 'action': constants.PRE_SCREEN_AND_RECOMMEND_KEYWORD})

        # Assert
        self.assertRedirects(response, f'{reverse("screening_index")}?filter={constants.PRE_SCREENED_AND_RECOMMENDED_FILTER}')
        song1.refresh_from_db()
        song2.refresh_from_db()
        self.assertIsNone(song1.claimed_by)
        self.assertIsNone(song2.claimed_by)
        self.assertIsNone(song1.claim_date)
        self.assertIsNone(song2.claim_date)
        self.assertEqual(NewSong.Flags.PRE_SCREENED_PLUS, song1.flag)
        self.assertEqual(NewSong.Flags.PRE_SCREENED_PLUS, song2.flag)
        self.assertEqual(self.user.profile, song1.flagged_by)
        self.assertEqual(self.user.profile, song2.flagged_by)

        events = ScreeningEvent.objects.filter(new_song=song1)
        self.assertEqual(events.count(), 1)
        event = events.first()
        self.assertEqual(event.profile, self.user.profile)
        self.assertEqual(event.type, ScreeningEvent.Types.APPLY_FLAG)
        self.assertEqual(f'Flag set to {NewSong.Flags.PRE_SCREENED_PLUS} by {self.user.profile.display_name} (was None)', event.content)

        events = ScreeningEvent.objects.filter(new_song=song2)
        self.assertEqual(events.count(), 1)
        event = events.first()
        self.assertEqual(event.profile, self.user.profile)
        self.assertEqual(event.type, ScreeningEvent.Types.APPLY_FLAG)
        self.assertEqual(f'Flag set to {NewSong.Flags.PRE_SCREENED_PLUS} by {self.user.profile.display_name} (was None)', event.content)

    def test_cannot_prescreen_and_recommend_unclaimed_songs(self):
        # Arrange
        song1 = upload_factories.NewSongFactory(filename=SONG_1_FILENAME)
        song2 = upload_factories.NewSongFactory(filename=SONG_2_FILENAME)

        # Act
        response = self.client.post(reverse('screening_action'), {'selected_songs': [song1.id, song2.id], 'action': constants.PRE_SCREEN_AND_RECOMMEND_KEYWORD})

        # Assert
        self.assertRedirects(response, reverse('screening_index'))
        song1.refresh_from_db()
        song2.refresh_from_db()
        self.assertIsNone(song1.claimed_by)
        self.assertIsNone(song2.claimed_by)
        self.assertIsNone(song1.claim_date)
        self.assertIsNone(song2.claim_date)
        self.assertIsNone(song1.flag)
        self.assertIsNone(song2.flag)

    def test_cannot_prescreen_and_recommend_songs_claimed_by_others(self):
        # Arrange
        other_user = factories.UserFactory()
        song1 = upload_factories.NewSongFactory(filename=SONG_1_FILENAME, claimed_by=other_user.profile)
        song2 = upload_factories.NewSongFactory(filename=SONG_2_FILENAME, claimed_by=other_user.profile)

        # Act
        response = self.client.post(reverse('screening_action'), {'selected_songs': [song1.id, song2.id], 'action': constants.PRE_SCREEN_AND_RECOMMEND_KEYWORD})

        # Assert
        self.assertRedirects(response, reverse('screening_index'))
        song1.refresh_from_db()
        song2.refresh_from_db()
        self.assertEqual(other_user.profile, song1.claimed_by)
        self.assertEqual(other_user.profile, song2.claimed_by)
        self.assertIsNone(song1.flag)
        self.assertIsNone(song2.flag)

    def test_can_flag_claimed_song_as_needing_second_opinion(self):
        # Arrange
        song1 = upload_factories.NewSongFactory(claimed_by=self.user.profile)
        song2 = upload_factories.NewSongFactory(claimed_by=self.user.profile)
        song3 = upload_factories.NewSongFactory(claimed_by=self.user.profile)

        # Act
        response = self.client.post(reverse('screening_action'), {'selected_songs': [song1.id, song2.id], 'action': constants.NEEDS_SECOND_OPINION_KEYWORD})

        # Assert
        self.assertRedirects(response, f'{reverse("screening_index")}?filter={constants.NEEDS_SECOND_OPINION_FILTER}')
        song1.refresh_from_db()
        song2.refresh_from_db()
        song3.refresh_from_db()
        self.assertEqual(NewSong.Flags.NEEDS_SECOND_OPINION, song1.flag)
        self.assertEqual(self.user.profile, song1.flagged_by)
        self.assertEqual(NewSong.Flags.NEEDS_SECOND_OPINION, song2.flag)
        self.assertEqual(self.user.profile, song2.flagged_by)
        self.assertIsNone(song3.flag)
        self.assertIsNone(song3.flagged_by)

        events = ScreeningEvent.objects.filter(new_song=song1)
        self.assertEqual(events.count(), 1)
        event = events.first()
        self.assertEqual(event.profile, self.user.profile)
        self.assertEqual(event.type, ScreeningEvent.Types.APPLY_FLAG)
        self.assertEqual(f'Flag set to {NewSong.Flags.NEEDS_SECOND_OPINION} by {self.user.profile.display_name} (was None)', event.content)

        events = ScreeningEvent.objects.filter(new_song=song2)
        self.assertEqual(events.count(), 1)
        event = events.first()
        self.assertEqual(event.profile, self.user.profile)
        self.assertEqual(event.type, ScreeningEvent.Types.APPLY_FLAG)
        self.assertEqual(f'Flag set to {NewSong.Flags.NEEDS_SECOND_OPINION} by {self.user.profile.display_name} (was None)', event.content)

        events = ScreeningEvent.objects.filter(new_song=song3)
        self.assertEqual(events.count(), 0)

    def test_cannot_flag_unclaimed_song_as_needing_second_opinion(self):
        # Arrange
        other_user = factories.UserFactory()
        song1 = upload_factories.NewSongFactory(claimed_by=other_user.profile)
        song2 = upload_factories.NewSongFactory()

        # Act
        response = self.client.post(reverse('screening_action'), {'selected_songs': [song1.id, song2.id], 'action': constants.NEEDS_SECOND_OPINION_KEYWORD})

        # Assert
        self.assertRedirects(response, reverse('screening_index'))
        song1.refresh_from_db()
        song2.refresh_from_db()
        self.assertIsNone(song1.flag)
        self.assertIsNone(song1.flagged_by)
        self.assertIsNone(song2.flag)
        self.assertIsNone(song2.flagged_by)

    def test_cannot_clear_flag_from_unclaimed_song(self):
        # Arrange
        song1 = upload_factories.NewSongFactory(flag=NewSong.Flags.PRE_SCREENED, flagged_by=self.user.profile)

        # Act
        response = self.client.post(reverse('screening_action'), {'selected_songs': [song1.id], 'action': constants.CLEAR_FLAG_KEYWORD})

        # Assert
        self.assertRedirects(response, reverse('screening_index'))
        song1.refresh_from_db()
        self.assertEqual(NewSong.Flags.PRE_SCREENED, song1.flag)
        self.assertEqual(self.user.profile, song1.flagged_by)

    def test_cannot_clear_flags_from_songs_claimed_by_others(self):
        # Arrange
        other_user = factories.UserFactory()
        song1 = upload_factories.NewSongFactory(flag=NewSong.Flags.PRE_SCREENED, flagged_by=self.user.profile, claimed_by=other_user.profile)

        # Act
        response = self.client.post(reverse('screening_action'), {'selected_songs': [song1.id], 'action': constants.CLEAR_FLAG_KEYWORD})

        # Assert
        self.assertRedirects(response, reverse('screening_index'))
        song1.refresh_from_db()
        self.assertEqual(NewSong.Flags.PRE_SCREENED, song1.flag)
        self.assertEqual(self.user.profile, song1.flagged_by)

    def test_can_clear_flags_from_songs_claimed_by_user(self):
        # Arrange
        other_user = factories.UserFactory()
        song1 = upload_factories.NewSongFactory(flag=NewSong.Flags.PRE_SCREENED, flagged_by=self.user.profile, claimed_by=self.user.profile)
        song2 = upload_factories.NewSongFactory(flag=NewSong.Flags.PRE_SCREENED, flagged_by=other_user.profile, claimed_by=self.user.profile)

        # Act
        response = self.client.post(reverse('screening_action'), {'selected_songs': [song1.id, song2.id], 'action': constants.CLEAR_FLAG_KEYWORD})

        # Assert
        self.assertRedirects(response, reverse('screening_index'))
        song1.refresh_from_db()
        self.assertIsNone(song1.flag)
        self.assertIsNone(song1.flagged_by)
        self.assertIsNone(song1.claimed_by)
        self.assertIsNone(song1.claim_date)
        song2.refresh_from_db()
        self.assertIsNone(song2.flag)
        self.assertIsNone(song2.flagged_by)
        self.assertIsNone(song2.claimed_by)
        self.assertIsNone(song2.claim_date)

        events = ScreeningEvent.objects.filter(new_song=song1)
        self.assertEqual(events.count(), 1)
        event = events.first()
        self.assertEqual(event.profile, self.user.profile)
        self.assertEqual(event.type, ScreeningEvent.Types.CLEAR_FLAG)
        self.assertEqual(f'Flag cleared by {self.user.profile.display_name} (previously set to {NewSong.Flags.PRE_SCREENED})', event.content)

        events = ScreeningEvent.objects.filter(new_song=song2)
        self.assertEqual(events.count(), 1)
        event = events.first()
        self.assertEqual(event.profile, self.user.profile)
        self.assertEqual(event.type, ScreeningEvent.Types.CLEAR_FLAG)
        self.assertEqual(f'Flag cleared by {self.user.profile.display_name} (previously set to {NewSong.Flags.PRE_SCREENED})', event.content)

class ApprovalActionValidationTests(TestCase):
    new_file_dir = settings.NEW_FILE_DIR
    main_archive_dir = settings.MAIN_ARCHIVE_DIR

    def setUp(self):
        self.user = factories.UserFactory()
        self.permission = Permission.objects.get(codename='can_approve_songs')
        self.user.user_permissions.add(self.permission)
        self.client.force_login(self.user)

    def test_cannot_approve_single_unclaimed_song(self):
        # Arrange
        song1 = upload_factories.NewSongFactory()

        # Act
        response = self.client.post(reverse('screening_action'), {'selected_songs': [song1.id], 'action': constants.APPROVE_KEYWORD})

        # Assert
        self.assertRedirects(response, reverse('screen_song', kwargs={'pk': song1.id}))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(1, len(messages))
        self.assertEqual(constants.MESSAGE_APPROVAL_REQUIRES_CLAIM, str(messages[0]))

    def test_cannot_approve_song_under_investigation(self):
        # Arrange
        song1 = upload_factories.NewSongFactory(claimed_by=self.user.profile, flag=NewSong.Flags.UNDER_INVESTIGATION)

        # Act
        response = self.client.post(reverse('screening_action'), {'selected_songs': [song1.id], 'action': constants.APPROVE_KEYWORD})

        # Assert
        self.assertRedirects(response, reverse('screen_song', kwargs={'pk': song1.id}))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(1, len(messages))
        self.assertEqual(constants.MESSAGE_CANNOT_APPROVE_UNDER_INVESTIGATION, str(messages[0]))

    def test_cannot_approve_possible_duplicate_song(self):
        # Arrange
        song1 = upload_factories.NewSongFactory(claimed_by=self.user.profile, flag=NewSong.Flags.POSSIBLE_DUPLICATE)

        # Act
        response = self.client.post(reverse('screening_action'), {'selected_songs': [song1.id], 'action': constants.APPROVE_KEYWORD})

        # Assert
        self.assertRedirects(response, reverse('screen_song', kwargs={'pk': song1.id}))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(1, len(messages))
        self.assertEqual(constants.MESSAGE_CANNOT_APPROVE_POSSIBLE_DUPLICATE, str(messages[0]))

    def test_song_with_duplicate_filename_in_main_archive_cannot_be_approved(self):
        # Arrange
        song_factories.SongFactory(filename=SONG_1_FILENAME, hash='1234567890')
        song1 = upload_factories.NewSongFactory(claimed_by=self.user.profile, filename=SONG_1_FILENAME, hash='0987654321')

        # Act
        response = self.client.post(reverse('screening_action'), {'selected_songs': [song1.id], 'action': constants.APPROVE_KEYWORD})

        # Assert
        self.assertRedirects(response, reverse('screen_song', kwargs={'pk': song1.id}))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(1, len(messages))
        self.assertEqual(constants.MESSAGE_CANNOT_APPROVE_DUPLICATE_FILENAME, str(messages[0]))

    def test_song_with_duplicate_hash_in_main_archive_cannot_be_approved(self):
        # Arrange
        song_factories.SongFactory(hash='1234567890', filename='song2.mod')
        song1 = upload_factories.NewSongFactory(claimed_by=self.user.profile, hash='1234567890', filename=SONG_1_FILENAME)

        # Act
        response = self.client.post(reverse('screening_action'), {'selected_songs': [song1.id], 'action': constants.APPROVE_KEYWORD})

        # Assert
        self.assertRedirects(response, reverse('screen_song', kwargs={'pk': song1.id}))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(1, len(messages))
        self.assertEqual(constants.MESSAGE_CANNOT_APPROVE_DUPLICATE_HASH, str(messages[0]))

    def test_cannot_bulk_approve_unless_all_songs_are_prescreened(self):
        # Arrange
        song1 = upload_factories.NewSongFactory(flag=NewSong.Flags.PRE_SCREENED)
        song2 = upload_factories.NewSongFactory(flag=NewSong.Flags.PRE_SCREENED)
        song3 = upload_factories.NewSongFactory()

        # Act
        response = self.client.post(reverse('screening_action'), {'selected_songs': [song1.id, song2.id, song3.id], 'action': constants.APPROVE_KEYWORD})

        # Assert
        self.assertRedirects(response, reverse('screening_index') + f'?filter={constants.PRE_SCREENED_FILTER}')
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(1, len(messages))
        self.assertEqual(constants.MESSAGE_ALL_SONGS_MUST_BE_PRESCREENED_FOR_BULK_APPROVAL, str(messages[0]))

    def test_cannot_bulk_approve_and_feature_unless_all_songs_are_prescreened(self):
        # Arrange
        song1 = upload_factories.NewSongFactory(flag=NewSong.Flags.PRE_SCREENED)
        song2 = upload_factories.NewSongFactory(flag=NewSong.Flags.PRE_SCREENED)
        song3 = upload_factories.NewSongFactory()

        # Act
        response = self.client.post(reverse('screening_action'), {'selected_songs': [song1.id, song2.id, song3.id], 'action': constants.APPROVE_AND_FEATURE_KEYWORD})

        # Assert
        self.assertRedirects(response, reverse('screening_index') + f'?filter={constants.PRE_SCREENED_FILTER}')
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(1, len(messages))
        self.assertEqual(constants.MESSAGE_ALL_SONGS_MUST_BE_PRESCREENED_FOR_BULK_APPROVAL, str(messages[0]))

    def test_cannot_bulk_approve_if_any_song_has_duplicate_filename(self):
        # Arrange
        song_factories.SongFactory(filename=SONG_1_FILENAME)
        song1 = upload_factories.NewSongFactory(flag=NewSong.Flags.PRE_SCREENED, filename=SONG_1_FILENAME, hash='0987654321')
        song2 = upload_factories.NewSongFactory(flag=NewSong.Flags.PRE_SCREENED, filename=SONG_2_FILENAME, hash='1234567890')

        # Act
        response = self.client.post(reverse('screening_action'), {'selected_songs': [song1.id, song2.id], 'action': constants.APPROVE_KEYWORD})

        # Assert
        self.assertRedirects(response, reverse('screening_index') + '?filter=pre_screened')
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(1, len(messages))
        self.assertEqual(constants.MESSAGE_ALL_SONGS_MUST_HAVE_UNIQUE_FILENAME_FOR_BULK_APPROVAL, str(messages[0]))

    def test_cannot_bulk_approve_if_any_song_has_duplicate_hash(self):
        # Arrange
        song_factories.SongFactory(hash='1234567890')
        song1 = upload_factories.NewSongFactory(flag=NewSong.Flags.PRE_SCREENED, filename=SONG_1_FILENAME, hash='0987654321')
        song2 = upload_factories.NewSongFactory(flag=NewSong.Flags.PRE_SCREENED, filename=SONG_2_FILENAME, hash='1234567890')

        # Act
        response = self.client.post(reverse('screening_action'), {'selected_songs': [song1.id, song2.id], 'action': constants.APPROVE_KEYWORD})

        # Assert
        self.assertRedirects(response, reverse('screening_index') + f'?filter={constants.PRE_SCREENED_FILTER}')
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(1, len(messages))
        self.assertEqual(constants.MESSAGE_ALL_SONGS_MUST_HAVE_UNIQUE_HASH_FOR_BULK_APPROVAL, str(messages[0]))

    def test_cannot_bulk_approve_if_any_song_is_claimed_by_somebody_else(self):
        # Arrange
        user = factories.UserFactory()
        other_user = factories.UserFactory()
        permission = Permission.objects.get(codename='can_approve_songs')
        user.user_permissions.add(permission)

        song1 = upload_factories.NewSongFactory(flag=NewSong.Flags.PRE_SCREENED, claimed_by=other_user.profile)
        song2 = upload_factories.NewSongFactory(flag=NewSong.Flags.PRE_SCREENED)
        song3 = upload_factories.NewSongFactory(flag=NewSong.Flags.PRE_SCREENED)

        # Act
        self.client.force_login(user)
        response = self.client.post(reverse('screening_action'), {'selected_songs': [song1.id, song2.id, song3.id], 'action': constants.APPROVE_KEYWORD})

        # Assert
        self.assertRedirects(response, reverse('screening_index') + f'?filter={constants.PRE_SCREENED_FILTER}')
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(1, len(messages))
        self.assertEqual(constants.MESSAGE_ALL_SONGS_MUST_NOT_BE_CLAIMED_BY_OTHERS_FOR_BULK_APPROVAL, str(messages[0]))

class ApprovalActionTests(TestCase):
    new_file_dir = settings.NEW_FILE_DIR
    main_archive_dir = settings.MAIN_ARCHIVE_DIR

    def setUp(self) -> None:
        self.user = factories.UserFactory()
        self.permission = Permission.objects.get(codename='can_approve_songs')
        self.user.user_permissions.add(self.permission)
        self.client.force_login(self.user)

    def tearDown(self):
        # Cleanup new_file_dir after each test
        for filename in os.listdir(self.new_file_dir):
            file_path = os.path.join(self.new_file_dir, filename)
            os.remove(file_path)

        # Empty all subdirectories of main_archive_dir and then delete them
        for entry in os.listdir(self.main_archive_dir):
            entry_path = os.path.join(self.main_archive_dir, entry)
            if os.path.isdir(entry_path):
                shutil.rmtree(entry_path)
            else:
                os.remove(entry_path)

    def make_song(self, claimed_by, song_hash, filename, song_format, uploader_profile, is_by_uploader=False, flag=None, title=None):
        if title is not None and title.strip() == "":
            song = upload_factories.NewSongFactory(
                title=title,
                claimed_by=claimed_by,
                hash=song_hash,
                filename=filename,
                format=song_format,
                uploader_profile=uploader_profile,
                is_by_uploader=is_by_uploader,
                flag=flag
            )
        else:
            song = upload_factories.NewSongFactory(
                claimed_by=claimed_by,
                hash=song_hash,
                filename=filename,
                format=song_format,
                uploader_profile=uploader_profile,
                is_by_uploader=is_by_uploader,
                flag=flag
            )

        # Create a dummy file to represent the uploaded file
        with open(f'{self.new_file_dir}/{song.filename}.zip', 'w', encoding='utf-8') as file:
            file.write('test')

        # Create a target directory for the song in the main archive directory
        subfolder = song.filename[0].upper()
        if subfolder.isdigit():
            subfolder = '1_9'

        target_directory = os.path.join(
            settings.MAIN_ARCHIVE_DIR,
            song.format.upper(),
            subfolder
        )
        os.makedirs(target_directory, exist_ok=True)

        return song

    def assert_song_added_to_archive(self, screened_song, expected_artists=None, featured=False, use_filename_as_title=False):
        song = Song.objects.get(hash=screened_song.hash)
        self.assertEqual(screened_song.filename, song.filename)
        expected_folder = '0_9' if screened_song.filename[0].isdigit() else screened_song.filename[0].upper()
        self.assertEqual(expected_folder, song.folder)
        self.assertEqual(screened_song.format.upper(), song.format)
        if use_filename_as_title:
            self.assertEqual(screened_song.filename, song.title)
        else:
            self.assertEqual(screened_song.title, song.title)
        self.assertEqual(screened_song.uploader_profile, song.uploaded_by)

        if expected_artists is None:
            self.assertEqual(0, len(song.artist_set.all()))
        else:
            self.assertEqual(len(expected_artists), len(song.artist_set.all()))
            for artist in expected_artists:
                self.assertIn(artist, song.artist_set.all())
                self.assertEqual(len(expected_artists), len(artist.songs.all()))
                self.assertIn(song, artist.songs.all())

        if featured:
            self.assertEqual(self.user.profile, song.featured_by)
        else:
            self.assertIsNone(song.featured_by)

        self.assertTrue(os.path.isfile(song.get_archive_path()))
        previous_location = f'{settings.NEW_FILE_DIR}/{song.filename}.zip'
        self.assertFalse(os.path.exists(previous_location))

    def test_single_song_is_added_to_archive_when_approved(self):
        # Arrange
        uploader = factories.UserFactory()
        song1 = self.make_song(self.user.profile, '0987654321', SONG_1_FILENAME, Song.Formats.MOD, uploader.profile)

        # Act
        response = self.client.post(reverse('screening_action'), {'selected_songs': [song1.id], 'action': constants.APPROVE_KEYWORD})

        # Assert
        self.assert_song_added_to_archive(song1)
        self.assertRedirects(response, reverse('view_song', kwargs={'pk': Song.objects.get(hash=song1.hash).id}))
    
    def test_single_song_with_numercal_filename_is_added_to_archive_when_approved(self):
        # Arrange
        uploader = factories.UserFactory()
        song1 = self.make_song(self.user.profile, '0987654321', '1.mod', Song.Formats.MOD, uploader.profile)

        # Act
        response = self.client.post(reverse('screening_action'), {'selected_songs': [song1.id], 'action': constants.APPROVE_KEYWORD})

        # Assert
        self.assert_song_added_to_archive(song1)
        self.assertRedirects(response, reverse('view_song', kwargs={'pk': Song.objects.get(hash=song1.hash).id}))

    def test_unclaimed_prescreened_song_is_added_to_archive_when_approved(self):
        # Arrange
        uploader = factories.UserFactory()
        song1 = self.make_song(None, '0987654321', SONG_1_FILENAME, Song.Formats.MOD, uploader.profile, flag=NewSong.Flags.PRE_SCREENED)

        # Act
        response = self.client.post(reverse('screening_action'), {'selected_songs': [song1.id], 'action': constants.APPROVE_KEYWORD})

        # Assert
        self.assert_song_added_to_archive(song1)
        self.assertRedirects(response, reverse('view_song', kwargs={'pk': Song.objects.get(hash=song1.hash).id}))

    def test_song_is_added_to_artist_profile_when_uploaded_by_artist(self):
        # Arrange
        uploader_profile = factories.UserFactory().profile
        artist = ArtistFactory(profile=uploader_profile)
        song1 = self.make_song(self.user.profile, '0987654321', SONG_1_FILENAME, Song.Formats.MOD, uploader_profile, is_by_uploader=True)

        # Act
        self.client.post(reverse('screening_action'), {'selected_songs': [song1.id], 'action': constants.APPROVE_KEYWORD})

        # Assert
        self.assert_song_added_to_archive(song1, [artist])

    def test_artist_profile_created_when_uploader_does_not_have_one_yet(self):
        # Arrange
        uploader_profile = factories.UserFactory().profile
        song1 = self.make_song(self.user.profile, '0987654321', SONG_1_FILENAME, Song.Formats.MOD, uploader_profile, is_by_uploader=True)

        # Act
        self.client.post(reverse('screening_action'), {'selected_songs': [song1.id], 'action': constants.APPROVE_KEYWORD})

        # Assert
        artist = uploader_profile.artist
        self.assert_song_added_to_archive(song1, [artist])

    def test_artist_profile_created_has_unique_username(self):
        # Arrange
        uploader_profile = factories.UserFactory(username='TrackerDude').profile
        ArtistFactory(name='TrackerDude')
        song1 = self.make_song(self.user.profile, '0987654321', SONG_1_FILENAME, Song.Formats.MOD, uploader_profile, is_by_uploader=True)

        # Act
        self.client.post(reverse('screening_action'), {'selected_songs': [song1.id], 'action': constants.APPROVE_KEYWORD})

        # Assert
        artist = uploader_profile.artist
        self.assert_song_added_to_archive(song1, [artist])
        self.assertEqual('TrackerDude', artist.name)

    def test_approves_multiple_songs(self):
        # Arrange
        uploader = factories.UserFactory()
        uploader_artist = ArtistFactory(profile=uploader.profile)
        second_uploader = factories.UserFactory()
        song1 = self.make_song(self.user.profile, '0987654321', SONG_1_FILENAME, Song.Formats.MOD, uploader.profile, flag=NewSong.Flags.PRE_SCREENED)
        song2 = self.make_song(self.user.profile, '1234567890', SONG_2_FILENAME, Song.Formats.MOD, uploader.profile, is_by_uploader=True, flag=NewSong.Flags.PRE_SCREENED)
        song3 = self.make_song(self.user.profile, '2345678901', SONG_3_FILENAME, Song.Formats.IT, second_uploader.profile, is_by_uploader=True, flag=NewSong.Flags.PRE_SCREENED)

        # Act
        response = self.client.post(reverse('screening_action'), {'selected_songs': [song1.id, song2.id, song3.id], 'action': constants.APPROVE_KEYWORD})

        # Assert
        self.assert_song_added_to_archive(song1)
        self.assert_song_added_to_archive(song2, [uploader_artist])
        self.assert_song_added_to_archive(song3, [second_uploader.profile.artist])

        self.assertEqual(3, Song.objects.count())
        self.assertEqual(0, NewSong.objects.count())

        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(1, len(messages))
        self.assertEqual(constants.MESSAGE_SONGS_APPROVED.format(3), str(messages[0]))
        self.assertRedirects(response, reverse('screening_index'))

    def test_approves_multiple_songs_with_pre_screened_plus_flag(self):
        # Arrange
        uploader = factories.UserFactory()
        uploader_artist = ArtistFactory(profile=uploader.profile)
        second_uploader = factories.UserFactory()
        song1 = self.make_song(self.user.profile, '0987654321', SONG_1_FILENAME, Song.Formats.MOD, uploader.profile, flag=NewSong.Flags.PRE_SCREENED_PLUS)
        song2 = self.make_song(self.user.profile, '1234567890', SONG_2_FILENAME, Song.Formats.MOD, uploader.profile, is_by_uploader=True, flag=NewSong.Flags.PRE_SCREENED_PLUS)
        song3 = self.make_song(self.user.profile, '2345678901', SONG_3_FILENAME, Song.Formats.IT, second_uploader.profile, is_by_uploader=True, flag=NewSong.Flags.PRE_SCREENED_PLUS)

        # Act
        response = self.client.post(reverse('screening_action'), {'selected_songs': [song1.id, song2.id, song3.id], 'action': constants.APPROVE_KEYWORD})

        # Assert
        self.assert_song_added_to_archive(song1)
        self.assert_song_added_to_archive(song2, [uploader_artist])
        self.assert_song_added_to_archive(song3, [second_uploader.profile.artist])

        self.assertEqual(3, Song.objects.count())
        self.assertEqual(0, NewSong.objects.count())

        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(1, len(messages))
        self.assertEqual(constants.MESSAGE_SONGS_APPROVED.format(3), str(messages[0]))
        self.assertRedirects(response, reverse('screening_index'))

    def test_single_song_is_added_to_archive_and_featured_when_approved(self):
        # Arrange
        uploader = factories.UserFactory()
        song1 = self.make_song(self.user.profile, '0987654321', SONG_1_FILENAME, Song.Formats.MOD, uploader.profile)

        # Act
        self.client.force_login(self.user)
        self.client.post(reverse('screening_action'), {'selected_songs': [song1.id], 'action': constants.APPROVE_AND_FEATURE_KEYWORD})

        # Assert
        self.assert_song_added_to_archive(song1, featured=True)

    def test_approves_and_features_multiple_songs(self):
        # Arrange
        uploader = factories.UserFactory()
        uploader_artist = ArtistFactory(profile=uploader.profile)
        second_uploader = factories.UserFactory()
        song1 = self.make_song(self.user.profile, '0987654321', SONG_1_FILENAME, Song.Formats.MOD, uploader.profile, flag=NewSong.Flags.PRE_SCREENED_PLUS)
        song2 = self.make_song(self.user.profile, '1234567890', SONG_2_FILENAME, Song.Formats.MOD, uploader.profile, is_by_uploader=True, flag=NewSong.Flags.PRE_SCREENED_PLUS)
        song3 = self.make_song(self.user.profile, '2345678901', SONG_3_FILENAME, Song.Formats.IT, second_uploader.profile, is_by_uploader=True, flag=NewSong.Flags.PRE_SCREENED_PLUS)

        # Act
        response = self.client.post(reverse('screening_action'), {'selected_songs': [song1.id, song2.id, song3.id], 'action': constants.APPROVE_AND_FEATURE_KEYWORD})

        # Assert
        self.assert_song_added_to_archive(song1, featured=True)
        self.assert_song_added_to_archive(song2, [uploader_artist], featured=True)
        self.assert_song_added_to_archive(song3, [second_uploader.profile.artist], featured=True)

        self.assertEqual(3, Song.objects.count())
        self.assertEqual(0, NewSong.objects.count())

        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(1, len(messages))
        self.assertEqual(constants.MESSAGE_SONGS_APPROVED.format(3), str(messages[0]))
        self.assertRedirects(response, reverse('screening_index'))
    
    def test_approved_song_with_blank_title_gets_filename_as_title(self):
        # Arrange
        uploader = factories.UserFactory()
        song1 = self.make_song(self.user.profile, '0987654321', SONG_1_FILENAME, Song.Formats.MOD, uploader.profile, title="")

        # Act
        self.client.force_login(self.user)
        self.client.post(reverse('screening_action'), {'selected_songs': [song1.id], 'action': constants.APPROVE_KEYWORD})

        # Assert
        self.assert_song_added_to_archive(song1, featured=False, use_filename_as_title=True)

class RejectActionTests(TestCase):
    def setUp(self) -> None:
        self.user = factories.UserFactory()
        self.permission = Permission.objects.get(codename='can_approve_songs')
        self.user.user_permissions.add(self.permission)
        self.client.force_login(self.user)

    def test_reject_one_song_redirects_to_rejection_page(self):
        # Arrange
        song1 = upload_factories.NewSongFactory()

        # Act
        response = self.client.post(reverse('screening_action'), {'selected_songs': [song1.id], 'action': constants.REJECT_KEYWORD})

        # Assert
        self.assertRedirects(response, f"{reverse('screening_reject')}?song_ids={song1.id}", target_status_code=302)

    def test_reject_multiple_songs_redirects_to_rejection_page(self):
        # Arrange
        song1 = upload_factories.NewSongFactory()
        song2 = upload_factories.NewSongFactory()

        # Act
        response = self.client.post(reverse('screening_action'), {'selected_songs': [song1.id, song2.id], 'action': constants.REJECT_KEYWORD})

        # Assert
        self.assertRedirects(response, f"{reverse('screening_reject')}?song_ids={song1.id},{song2.id}", target_status_code=302)

class RenameActionTests(TestCase):
    def setUp(self) -> None:
        self.user = factories.UserFactory()
        self.permission = Permission.objects.get(codename='can_approve_songs')
        self.user.user_permissions.add(self.permission)
        self.client.force_login(self.user)

    def test_cannot_rename_unclaimed_song(self):
        # Arrange
        song1 = upload_factories.NewSongFactory()

        # Act
        response = self.client.post(reverse('screening_action'), {'selected_songs': [song1.id], 'action': constants.RENAME_KEYWORD})

        # Assert
        self.assertRedirects(response, reverse('screen_song', kwargs={'pk': song1.id}))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(1, len(messages))
        self.assertEqual(constants.RENAME_SCREENING_REQUIRES_CLAIM, str(messages[0]))

    def test_cannot_rename_multiple_songs(self):
        # Arrange
        song1 = upload_factories.NewSongFactory(claimed_by=self.user.profile)
        song2 = upload_factories.NewSongFactory(claimed_by=self.user.profile)

        # Act
        response = self.client.post(reverse('screening_action'), {'selected_songs': [song1.id, song2.id], 'action': constants.RENAME_KEYWORD})

        # Assert
        self.assertRedirects(response, reverse('screen_song', kwargs={'pk': song1.id}))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(1, len(messages))
        self.assertEqual(constants.RENAME_SCREENING_ONE_SONG_ONLY, str(messages[0]))

    def test_rename_one_song_redirects_to_rename_page(self):
        # Arrange
        song1 = upload_factories.NewSongFactory(claimed_by=self.user.profile)

        # Act
        response = self.client.post(reverse('screening_action'), {'selected_songs': [song1.id], 'action': constants.RENAME_KEYWORD})

        # Assert
        self.assertRedirects(response, f"{reverse('screening_rename', kwargs = {'pk': song1.id})}")
