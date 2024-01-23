import os

from django.conf import settings
from django.contrib.messages import get_messages
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls.base import reverse

from homepage.tests import factories
from songs import factories as song_factories
from songs.models import NewSong, Song
from songs import constants
from artists.factories import ArtistFactory

SONG_1_FILENAME = 'song1.mod'
SONG_2_FILENAME = 'song2.mod'

class ScreeningActionViewTests(TestCase):
    new_file_dir = settings.NEW_FILE_DIR
    main_archive_dir = settings.MAIN_ARCHIVE_DIR

    def tearDown(self):
        # Cleanup new_file_dir after each test
        for filename in os.listdir(self.new_file_dir):
            file_path = os.path.join(self.new_file_dir, filename)
            os.remove(file_path)

        # Empty all subdirectories of main_archive_dir and then delete them
        for directory in os.listdir(self.main_archive_dir):
            directory_path = os.path.join(self.main_archive_dir, directory)
            for filename in os.listdir(directory_path):
                file_path = os.path.join(directory_path, filename)
                os.remove(file_path)
            os.rmdir(directory_path)

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

    def test_screener_can_claim_single_unclaimed_song(self):
        # Arrange
        user = factories.UserFactory()
        permission = Permission.objects.get(codename='can_approve_songs')
        user.user_permissions.add(permission)
        song1 = song_factories.NewSongFactory(filename=SONG_1_FILENAME)

        # Act
        self.client.force_login(user)
        response = self.client.post(reverse('screening_action'), {'selected_songs': [song1.id], 'action': constants.CLAIM_KEYWORD})

        # Assert
        self.assertRedirects(response, reverse('screening_index'))
        song1.refresh_from_db()
        self.assertEqual(user.profile, song1.claimed_by)
        self.assertIsNotNone(song1.claim_date)

    def test_screener_can_claim_multiple_unclaimed_songs(self):
        # Arrange
        user = factories.UserFactory()
        permission = Permission.objects.get(codename='can_approve_songs')
        user.user_permissions.add(permission)
        song1 = song_factories.NewSongFactory(filename=SONG_1_FILENAME)
        song2 = song_factories.NewSongFactory(filename=SONG_2_FILENAME)

        # Act
        self.client.force_login(user)
        response = self.client.post(reverse('screening_action'), {'selected_songs': [song1.id, song2.id], 'action': constants.CLAIM_KEYWORD})

        # Assert
        self.assertRedirects(response, reverse('screening_index'))
        song1.refresh_from_db()
        song2.refresh_from_db()
        self.assertEqual(user.profile, song1.claimed_by)
        self.assertIsNotNone(song1.claim_date)
        self.assertEqual(user.profile, song2.claimed_by)
        self.assertIsNotNone(song2.claim_date)

    def test_cannot_claim_songs_already_claimed_by_others(self):
        # Arrange
        user = factories.UserFactory()
        other_user = factories.UserFactory()
        permission = Permission.objects.get(codename='can_approve_songs')
        user.user_permissions.add(permission)
        song1 = song_factories.NewSongFactory(filename=SONG_1_FILENAME, claimed_by=other_user.profile)
        song2 = song_factories.NewSongFactory(filename=SONG_2_FILENAME, claimed_by=other_user.profile)

        # Act
        self.client.force_login(user)
        response = self.client.post(reverse('screening_action'), {'selected_songs': [song1.id, song2.id], 'action': constants.CLAIM_KEYWORD})

        # Assert
        self.assertRedirects(response, reverse('screening_index'))
        song1.refresh_from_db()
        song2.refresh_from_db()
        self.assertEqual(other_user.profile, song1.claimed_by)
        self.assertEqual(other_user.profile, song2.claimed_by)

    def test_can_prescreen_claimed_songs(self):
        # Arrange
        user = factories.UserFactory()
        permission = Permission.objects.get(codename='can_approve_songs')
        user.user_permissions.add(permission)
        song1 = song_factories.NewSongFactory(filename=SONG_1_FILENAME, claimed_by=user.profile)
        song2 = song_factories.NewSongFactory(filename=SONG_2_FILENAME, claimed_by=user.profile)

        # Act
        self.client.force_login(user)
        response = self.client.post(reverse('screening_action'), {'selected_songs': [song1.id, song2.id], 'action': constants.PRE_SCREEN_KEYWORD})

        # Assert
        self.assertRedirects(response, reverse('screening_index'))
        song1.refresh_from_db()
        song2.refresh_from_db()
        self.assertIsNone(song1.claimed_by)
        self.assertIsNone(song2.claimed_by)
        self.assertIsNone(song1.claim_date)
        self.assertIsNone(song2.claim_date)
        self.assertEqual(NewSong.Flags.PRE_SCREENED, song1.flag)
        self.assertEqual(NewSong.Flags.PRE_SCREENED, song2.flag)
        self.assertEqual(user.profile, song1.flagged_by)
        self.assertEqual(user.profile, song2.flagged_by)

    def test_cannot_prescreen_unclaimed_songs(self):
        # Arrange
        user = factories.UserFactory()
        permission = Permission.objects.get(codename='can_approve_songs')
        user.user_permissions.add(permission)
        song1 = song_factories.NewSongFactory(filename=SONG_1_FILENAME)
        song2 = song_factories.NewSongFactory(filename=SONG_2_FILENAME)

        # Act
        self.client.force_login(user)
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
        user = factories.UserFactory()
        other_user = factories.UserFactory()
        permission = Permission.objects.get(codename='can_approve_songs')
        user.user_permissions.add(permission)
        song1 = song_factories.NewSongFactory(filename=SONG_1_FILENAME, claimed_by=other_user.profile)
        song2 = song_factories.NewSongFactory(filename=SONG_2_FILENAME, claimed_by=other_user.profile)

        # Act
        self.client.force_login(user)
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
        user = factories.UserFactory()
        permission = Permission.objects.get(codename='can_approve_songs')
        user.user_permissions.add(permission)
        song1 = song_factories.NewSongFactory(filename=SONG_1_FILENAME, claimed_by=user.profile)
        song2 = song_factories.NewSongFactory(filename=SONG_2_FILENAME, claimed_by=user.profile)

        # Act
        self.client.force_login(user)
        response = self.client.post(reverse('screening_action'), {'selected_songs': [song1.id, song2.id], 'action': constants.PRE_SCREEN_AND_RECOMMEND_KEYWORD})

        # Assert
        self.assertRedirects(response, reverse('screening_index'))
        song1.refresh_from_db()
        song2.refresh_from_db()
        self.assertIsNone(song1.claimed_by)
        self.assertIsNone(song2.claimed_by)
        self.assertIsNone(song1.claim_date)
        self.assertIsNone(song2.claim_date)
        self.assertEqual(NewSong.Flags.PRE_SCREENED_PLUS, song1.flag)
        self.assertEqual(NewSong.Flags.PRE_SCREENED_PLUS, song2.flag)
        self.assertEqual(user.profile, song1.flagged_by)
        self.assertEqual(user.profile, song2.flagged_by)

    def test_cannot_prescreen_and_recommend_unclaimed_songs(self):
        # Arrange
        user = factories.UserFactory()
        permission = Permission.objects.get(codename='can_approve_songs')
        user.user_permissions.add(permission)
        song1 = song_factories.NewSongFactory(filename=SONG_1_FILENAME)
        song2 = song_factories.NewSongFactory(filename=SONG_2_FILENAME)

        # Act
        self.client.force_login(user)
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
        user = factories.UserFactory()
        other_user = factories.UserFactory()
        permission = Permission.objects.get(codename='can_approve_songs')
        user.user_permissions.add(permission)
        song1 = song_factories.NewSongFactory(filename=SONG_1_FILENAME, claimed_by=other_user.profile)
        song2 = song_factories.NewSongFactory(filename=SONG_2_FILENAME, claimed_by=other_user.profile)

        # Act
        self.client.force_login(user)
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
        user = factories.UserFactory()
        permission = Permission.objects.get(codename='can_approve_songs')
        user.user_permissions.add(permission)
        song1 = song_factories.NewSongFactory(claimed_by=user.profile)
        song2 = song_factories.NewSongFactory(claimed_by=user.profile)
        song3 = song_factories.NewSongFactory(claimed_by=user.profile)

        # Act
        self.client.force_login(user)
        response = self.client.post(reverse('screening_action'), {'selected_songs': [song1.id, song2.id], 'action': constants.NEEDS_SECOND_OPINION_KEYWORD})

        # Assert
        self.assertRedirects(response, reverse('screening_index'))
        song1.refresh_from_db()
        song2.refresh_from_db()
        song3.refresh_from_db()
        self.assertEqual(NewSong.Flags.NEEDS_SECOND_OPINION, song1.flag)
        self.assertEqual(user.profile, song1.flagged_by)
        self.assertEqual(NewSong.Flags.NEEDS_SECOND_OPINION, song2.flag)
        self.assertEqual(user.profile, song2.flagged_by)
        self.assertIsNone(song3.flag)
        self.assertIsNone(song3.flagged_by)

    def test_cannot_flag_unclaimed_song_as_needing_second_opinion(self):
        # Arrange
        user = factories.UserFactory()
        permission = Permission.objects.get(codename='can_approve_songs')
        user.user_permissions.add(permission)
        other_user = factories.UserFactory()
        song1 = song_factories.NewSongFactory(claimed_by=other_user.profile)
        song2 = song_factories.NewSongFactory()

        # Act
        self.client.force_login(user)
        response = self.client.post(reverse('screening_action'), {'selected_songs': [song1.id, song2.id], 'action': constants.NEEDS_SECOND_OPINION_KEYWORD})

        # Assert
        self.assertRedirects(response, reverse('screening_index'))
        song1.refresh_from_db()
        song2.refresh_from_db()        
        self.assertIsNone(song1.flag)
        self.assertIsNone(song1.flagged_by)
        self.assertIsNone(song2.flag)
        self.assertIsNone(song2.flagged_by)

    def test_cannot_claim_song_needing_second_opinion_when_flagged_by_self(self):
        # Arrange
        user = factories.UserFactory()
        permission = Permission.objects.get(codename='can_approve_songs')
        user.user_permissions.add(permission)
        song1 = song_factories.NewSongFactory(flag=NewSong.Flags.NEEDS_SECOND_OPINION, flagged_by=user.profile)
        song2 = song_factories.NewSongFactory(flag=NewSong.Flags.NEEDS_SECOND_OPINION, flagged_by=user.profile)

        # Act
        self.client.force_login(user)
        response = self.client.post(reverse('screening_action'), {'selected_songs': [song1.id, song2.id], 'action': constants.CLAIM_KEYWORD})

        # Assert
        self.assertRedirects(response, reverse('screening_index'))
        song1.refresh_from_db()
        song2.refresh_from_db()
        self.assertIsNone(song1.claimed_by)
        self.assertEqual(user.profile, song1.flagged_by)
        self.assertEqual(NewSong.Flags.NEEDS_SECOND_OPINION, song1.flag)
        self.assertIsNone(song2.claimed_by)
        self.assertEqual(user.profile, song2.flagged_by)
        self.assertEqual(NewSong.Flags.NEEDS_SECOND_OPINION, song2.flag)

    def test_can_flag_claimed_song_as_possible_duplicate(self):
        # Arrange
        user = factories.UserFactory()
        permission = Permission.objects.get(codename='can_approve_songs')
        user.user_permissions.add(permission)

        song1 = song_factories.NewSongFactory(claimed_by=user.profile)
        song2 = song_factories.NewSongFactory(claimed_by=user.profile)
        song3 = song_factories.NewSongFactory(claimed_by=user.profile)

        # Act
        self.client.force_login(user)
        response = self.client.post(reverse('screening_action'), {'selected_songs': [song1.id], 'action': constants.POSSIBLE_DUPLICATE_KEYWORD})

        # Assert
        self.assertRedirects(response, reverse('screening_index'))
        song1.refresh_from_db()
        song2.refresh_from_db()
        song3.refresh_from_db()
        self.assertEqual(NewSong.Flags.POSSIBLE_DUPLICATE, song1.flag)
        self.assertEqual(user.profile, song1.flagged_by)
        self.assertIsNone(song2.flag)
        self.assertIsNone(song2.flagged_by)
        self.assertIsNone(song3.flag)
        self.assertIsNone(song3.flagged_by)

    def test_cannot_flag_unclaimed_song_as_possible_duplicate(self):
        # Arrange
        user = factories.UserFactory()
        permission = Permission.objects.get(codename='can_approve_songs')
        user.user_permissions.add(permission)

        song1 = song_factories.NewSongFactory()

        # Act
        self.client.force_login(user)
        response = self.client.post(reverse('screening_action'), {'selected_songs': [song1.id], 'action': constants.POSSIBLE_DUPLICATE_KEYWORD})

        # Assert
        self.assertRedirects(response, reverse('screening_index'))
        song1.refresh_from_db()
        self.assertIsNone(song1.flag)
        self.assertIsNone(song1.flagged_by)

    def test_cannot_flag_song_claimed_by_others_as_possible_duplicate(self):
        # Arrange
        user = factories.UserFactory()
        other_user = factories.UserFactory()
        permission = Permission.objects.get(codename='can_approve_songs')
        user.user_permissions.add(permission)

        song1 = song_factories.NewSongFactory(claimed_by=other_user.profile)

        # Act
        self.client.force_login(user)
        response = self.client.post(reverse('screening_action'), {'selected_songs': [song1.id], 'action': constants.POSSIBLE_DUPLICATE_KEYWORD})

        # Assert
        self.assertRedirects(response, reverse('screening_index'))
        song1.refresh_from_db()
        self.assertIsNone(song1.flag)
        self.assertIsNone(song1.flagged_by)

    def test_cannot_claim_song_flagged_as_possible_duplicate_by_self(self):
        # Arrange
        user = factories.UserFactory()
        permission = Permission.objects.get(codename='can_approve_songs')
        user.user_permissions.add(permission)

        song1 = song_factories.NewSongFactory(flag=NewSong.Flags.POSSIBLE_DUPLICATE, flagged_by=user.profile)

        # Act
        self.client.force_login(user)
        response = self.client.post(reverse('screening_action'), {'selected_songs': [song1.id], 'action': constants.CLAIM_KEYWORD})

        # Assert
        self.assertRedirects(response, reverse('screening_index'))
        song1.refresh_from_db()
        self.assertIsNone(song1.claimed_by)
        self.assertEqual(user.profile, song1.flagged_by)
        self.assertEqual(NewSong.Flags.POSSIBLE_DUPLICATE, song1.flag)

    def test_can_flag_claimed_song_as_under_investigation(self):
        # Arrange
        user = factories.UserFactory()
        permission = Permission.objects.get(codename='can_approve_songs')
        user.user_permissions.add(permission)

        song1 = song_factories.NewSongFactory(claimed_by=user.profile)

        # Act
        self.client.force_login(user)
        response = self.client.post(reverse('screening_action'), {'selected_songs': [song1.id], 'action': constants.UNDER_INVESTIGATION_KEYWORD})

        # Assert
        self.assertRedirects(response, reverse('screening_index'))
        song1.refresh_from_db()
        self.assertEqual(NewSong.Flags.UNDER_INVESTIGATION, song1.flag)
        self.assertEqual(user.profile, song1.flagged_by)

    def test_cannot_flag_unclaimed_song_as_under_investigation(self):
        # Arrange
        user = factories.UserFactory()
        permission = Permission.objects.get(codename='can_approve_songs')
        user.user_permissions.add(permission)

        song1 = song_factories.NewSongFactory()

        # Act
        self.client.force_login(user)
        response = self.client.post(reverse('screening_action'), {'selected_songs': [song1.id], 'action': constants.UNDER_INVESTIGATION_KEYWORD})

        # Assert
        self.assertRedirects(response, reverse('screening_index'))
        song1.refresh_from_db()
        self.assertIsNone(song1.flag)
        self.assertIsNone(song1.flagged_by)

    def test_cannot_flag_song_claimed_by_others_as_under_investigation(self):
        # Arrange
        user = factories.UserFactory()
        other_user = factories.UserFactory()
        permission = Permission.objects.get(codename='can_approve_songs')
        user.user_permissions.add(permission)

        song1 = song_factories.NewSongFactory(claimed_by=other_user.profile)

        # Act
        self.client.force_login(user)
        response = self.client.post(reverse('screening_action'), {'selected_songs': [song1.id], 'action': constants.UNDER_INVESTIGATION_KEYWORD})

        # Assert
        self.assertRedirects(response, reverse('screening_index'))
        song1.refresh_from_db()
        self.assertIsNone(song1.flag)
        self.assertIsNone(song1.flagged_by)

    def test_cannot_claim_song_flagged_as_under_investigation_by_self(self):
        # Arrange
        user = factories.UserFactory()
        permission = Permission.objects.get(codename='can_approve_songs')
        user.user_permissions.add(permission)

        song1 = song_factories.NewSongFactory(flag=NewSong.Flags.UNDER_INVESTIGATION, flagged_by=user.profile)

        # Act
        self.client.force_login(user)
        response = self.client.post(reverse('screening_action'), {'selected_songs': [song1.id], 'action': constants.CLAIM_KEYWORD})

        # Assert
        self.assertRedirects(response, reverse('screening_index'))
        song1.refresh_from_db()
        self.assertIsNone(song1.claimed_by)
        self.assertEqual(user.profile, song1.flagged_by)
        self.assertEqual(NewSong.Flags.UNDER_INVESTIGATION, song1.flag)

    def test_cannot_approve_single_unclaimed_song(self):
        # Arrange
        user = factories.UserFactory()
        permission = Permission.objects.get(codename='can_approve_songs')
        user.user_permissions.add(permission)

        song1 = song_factories.NewSongFactory()

        # Act
        self.client.force_login(user)
        response = self.client.post(reverse('screening_action'), {'selected_songs': [song1.id], 'action': constants.APPROVE_KEYWORD})

        # Assert
        self.assertRedirects(response, reverse('screen_song', kwargs={'pk': song1.id}))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(1, len(messages))
        self.assertEqual(constants.MESSAGE_APPROVAL_REQUIRES_CLAIM, str(messages[0]))

    def test_cannot_approve_song_under_investigation(self):
        # Arrange
        user = factories.UserFactory()
        permission = Permission.objects.get(codename='can_approve_songs')
        user.user_permissions.add(permission)

        song1 = song_factories.NewSongFactory(claimed_by=user.profile, flag=NewSong.Flags.UNDER_INVESTIGATION)

        # Act
        self.client.force_login(user)
        response = self.client.post(reverse('screening_action'), {'selected_songs': [song1.id], 'action': constants.APPROVE_KEYWORD})

        # Assert
        self.assertRedirects(response, reverse('screen_song', kwargs={'pk': song1.id}))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(1, len(messages))
        self.assertEqual(constants.MESSAGE_CANNOT_APPROVE_UNDER_INVESTIGATION, str(messages[0]))

    def test_cannot_approve_possible_duplicate_song(self):
        # Arrange
        user = factories.UserFactory()
        permission = Permission.objects.get(codename='can_approve_songs')
        user.user_permissions.add(permission)

        song1 = song_factories.NewSongFactory(claimed_by=user.profile, flag=NewSong.Flags.POSSIBLE_DUPLICATE)

        # Act
        self.client.force_login(user)
        response = self.client.post(reverse('screening_action'), {'selected_songs': [song1.id], 'action': constants.APPROVE_KEYWORD})

        # Assert
        self.assertRedirects(response, reverse('screen_song', kwargs={'pk': song1.id}))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(1, len(messages))
        self.assertEqual(constants.MESSAGE_CANNOT_APPROVE_POSSIBLE_DUPLICATE, str(messages[0]))

    def test_song_with_duplicate_filename_in_main_archive_cannot_be_approved(self):
        # Arrange
        user = factories.UserFactory()
        permission = Permission.objects.get(codename='can_approve_songs')
        user.user_permissions.add(permission)

        song_factories.SongFactory(filename=SONG_1_FILENAME, hash='1234567890')
        song1 = song_factories.NewSongFactory(claimed_by=user.profile, filename=SONG_1_FILENAME, hash='0987654321')

        # Act
        self.client.force_login(user)
        response = self.client.post(reverse('screening_action'), {'selected_songs': [song1.id], 'action': constants.APPROVE_KEYWORD})

        # Assert
        self.assertRedirects(response, reverse('screen_song', kwargs={'pk': song1.id}))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(1, len(messages))
        self.assertEqual(constants.MESSAGE_CANNOT_APPROVE_DUPLICATE_FILENAME, str(messages[0]))

    def test_song_with_duplicate_hash_in_main_archive_cannot_be_approved(self):
        # Arrange
        user = factories.UserFactory()
        permission = Permission.objects.get(codename='can_approve_songs')
        user.user_permissions.add(permission)

        song_factories.SongFactory(hash='1234567890', filename='song2.mod')
        song1 = song_factories.NewSongFactory(claimed_by=user.profile, hash='1234567890', filename=SONG_1_FILENAME)

        # Act
        self.client.force_login(user)
        response = self.client.post(reverse('screening_action'), {'selected_songs': [song1.id], 'action': constants.APPROVE_KEYWORD})

        # Assert
        self.assertRedirects(response, reverse('screen_song', kwargs={'pk': song1.id}))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(1, len(messages))
        self.assertEqual(constants.MESSAGE_CANNOT_APPROVE_DUPLICATE_HASH, str(messages[0]))

    def test_single_song_is_added_to_archive_when_approved(self):
        # Arrange
        user = factories.UserFactory()
        uploader = factories.UserFactory()
        permission = Permission.objects.get(codename='can_approve_songs')
        user.user_permissions.add(permission)
        song1 = song_factories.NewSongFactory(claimed_by=user.profile, hash='0987654321', filename=SONG_1_FILENAME, format='mod', uploader_profile=uploader.profile)

        # Put a file in the new_file_dir called test.mod.zip - doesn't matter what it contains
        with open(f'{self.new_file_dir}/{SONG_1_FILENAME}.zip', 'w', encoding='utf-8') as file:
            file.write('test')
        # Create an S folder in the main archive dir
        os.mkdir(f'{settings.MAIN_ARCHIVE_DIR}/S')

        # Act
        self.client.force_login(user)
        response = self.client.post(reverse('screening_action'), {'selected_songs': [song1.id], 'action': constants.APPROVE_KEYWORD})

        # Assert
        song = Song.objects.get(hash=song1.hash)
        self.assertEqual('0987654321', song.hash)
        self.assertEqual(SONG_1_FILENAME, song.filename)
        self.assertEqual('S', song.folder)
        self.assertEqual(Song.Formats.MOD, song.format)
        self.assertEqual(song1.title, song.title)
        self.assertEqual(uploader.profile, song.uploaded_by)

        self.assertRedirects(response, reverse('view_song', kwargs={'pk': song.id}))
        file_location = f'{settings.MAIN_ARCHIVE_DIR}/{song.folder}/{song.filename}.zip'
        self.assertTrue(os.path.isfile(file_location))
        previous_location = f'{settings.NEW_FILE_DIR}/{song.filename}.zip'
        self.assertFalse(os.path.exists(previous_location))
        self.assertFalse(NewSong.objects.filter(id=song1.id).exists())

    def test_song_is_added_to_artist_profile_when_uploaded_by_artist(self):
        # Arrange
        user = factories.UserFactory()
        permission = Permission.objects.get(codename='can_approve_songs')
        user.user_permissions.add(permission)
        uploader_profile = factories.UserFactory().profile
        artist = ArtistFactory(profile=uploader_profile)
        song1 = song_factories.NewSongFactory(
            claimed_by=user.profile,
            hash='0987654321',
            filename=SONG_1_FILENAME,
            format='mod',
            is_by_uploader=True,
            uploader_profile=uploader_profile
        )

        # Put a file in the new_file_dir called test.mod.zip - doesn't matter what it contains
        with open(f'{self.new_file_dir}/{SONG_1_FILENAME}.zip', 'w', encoding='utf-8') as file:
            file.write('test')
        # Create an S folder in the main archive dir
        os.mkdir(f'{settings.MAIN_ARCHIVE_DIR}/S')

        # Act
        self.client.force_login(user)
        self.client.post(reverse('screening_action'), {'selected_songs': [song1.id], 'action': constants.APPROVE_KEYWORD})

        # Assert
        song = Song.objects.get(hash=song1.hash)
        self.assertEqual(uploader_profile, song.uploaded_by)
        self.assertEqual(1, len(song.artist_set.all()))
        self.assertIn(artist, song.artist_set.all())
        self.assertEqual(1, len(artist.songs.all()))
        self.assertIn(song, artist.songs.all())

    def test_artist_profile_created_when_uploader_does_not_have_one_yet(self):
        # Arrange
        user = factories.UserFactory()
        permission = Permission.objects.get(codename='can_approve_songs')
        user.user_permissions.add(permission)
        uploader_profile = factories.UserFactory().profile
        song1 = song_factories.NewSongFactory(
            claimed_by=user.profile,
            hash='0987654321',
            filename=SONG_1_FILENAME,
            format='mod',
            is_by_uploader=True,
            uploader_profile=uploader_profile
        )

        # Put a file in the new_file_dir called test.mod.zip - doesn't matter what it contains
        with open(f'{self.new_file_dir}/{SONG_1_FILENAME}.zip', 'w', encoding='utf-8') as file:
            file.write('test')
        # Create an S folder in the main archive dir
        os.mkdir(f'{settings.MAIN_ARCHIVE_DIR}/S')

        # Act
        self.client.force_login(user)
        self.client.post(reverse('screening_action'), {'selected_songs': [song1.id], 'action': constants.APPROVE_KEYWORD})

        # Assert
        song = Song.objects.get(hash=song1.hash)
        artist = uploader_profile.artist
        self.assertEqual(uploader_profile.display_name, artist.name)
        self.assertEqual(uploader_profile, song.uploaded_by)
        self.assertEqual(1, len(song.artist_set.all()))
        self.assertIn(artist, song.artist_set.all())
        self.assertEqual(1, len(artist.songs.all()))
        self.assertIn(song, artist.songs.all())

    def test_artist_profile_created_has_unique_username(self):
        # Arrange
        user = factories.UserFactory()
        permission = Permission.objects.get(codename='can_approve_songs')
        user.user_permissions.add(permission)
        uploader_profile = factories.UserFactory(username='TrackerDude').profile
        ArtistFactory(name='TrackerDude')
        song1 = song_factories.NewSongFactory(
            claimed_by=user.profile,
            hash='0987654321',
            filename=SONG_1_FILENAME,
            format='mod',
            is_by_uploader=True,
            uploader_profile=uploader_profile
        )

        # Put a file in the new_file_dir called test.mod.zip - doesn't matter what it contains
        with open(f'{self.new_file_dir}/{SONG_1_FILENAME}.zip', 'w', encoding='utf-8') as file:
            file.write('test')
        # Create an S folder in the main archive dir
        os.mkdir(f'{settings.MAIN_ARCHIVE_DIR}/S')

        # Act
        self.client.force_login(user)
        self.client.post(reverse('screening_action'), {'selected_songs': [song1.id], 'action': constants.APPROVE_KEYWORD})

        # Assert
        song = Song.objects.get(hash=song1.hash)
        artist = uploader_profile.artist
        self.assertEqual(uploader_profile, song.uploaded_by)
        self.assertEqual('TrackerDude', artist.name)
        self.assertEqual(1, len(song.artist_set.all()))
        self.assertIn(artist, song.artist_set.all())
        self.assertEqual(1, len(artist.songs.all()))
        self.assertIn(song, artist.songs.all())

    def test_cannot_bulk_approve_unless_all_songs_are_prescreened(self):
        # Arrange
        user = factories.UserFactory()
        permission = Permission.objects.get(codename='can_approve_songs')
        user.user_permissions.add(permission)

        song1 = song_factories.NewSongFactory(flag=NewSong.Flags.PRE_SCREENED)
        song2 = song_factories.NewSongFactory(flag=NewSong.Flags.PRE_SCREENED)
        song3 = song_factories.NewSongFactory()

        # Act
        self.client.force_login(user)
        response = self.client.post(reverse('screening_action'), {'selected_songs': [song1.id, song2.id, song3.id], 'action': constants.APPROVE_KEYWORD})

        # Assert
        self.assertRedirects(response, reverse('screening_index') + '?filter=pre_screened')
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(1, len(messages))
        self.assertEqual(constants.MESSAGE_ALL_SONGS_MUST_BE_PRESCREENED_FOR_BULK_APPROVAL, str(messages[0]))

    def test_cannot_bulk_approve_if_any_song_has_duplicate_filename(self):
        # Arrange
        user = factories.UserFactory()
        permission = Permission.objects.get(codename='can_approve_songs')
        user.user_permissions.add(permission)

        song_factories.SongFactory(filename=SONG_1_FILENAME)
        song1 = song_factories.NewSongFactory(flag=NewSong.Flags.PRE_SCREENED, filename=SONG_1_FILENAME, hash='0987654321')
        song2 = song_factories.NewSongFactory(flag=NewSong.Flags.PRE_SCREENED, filename=SONG_2_FILENAME, hash='1234567890')

        # Act
        self.client.force_login(user)
        response = self.client.post(reverse('screening_action'), {'selected_songs': [song1.id, song2.id], 'action': constants.APPROVE_KEYWORD})

        # Assert
        self.assertRedirects(response, reverse('screening_index') + '?filter=pre_screened')
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(1, len(messages))
        self.assertEqual(constants.MESSAGE_ALL_SONGS_MUST_HAVE_UNIQUE_FILENAME_FOR_BULK_APPROVAL, str(messages[0]))

    def test_cannot_bulk_approve_if_any_song_has_duplicate_hash(self):
        # Arrange
        user = factories.UserFactory()
        permission = Permission.objects.get(codename='can_approve_songs')
        user.user_permissions.add(permission)

        song_factories.SongFactory(hash='1234567890')
        song1 = song_factories.NewSongFactory(flag=NewSong.Flags.PRE_SCREENED, filename=SONG_1_FILENAME, hash='0987654321')
        song2 = song_factories.NewSongFactory(flag=NewSong.Flags.PRE_SCREENED, filename=SONG_2_FILENAME, hash='1234567890')

        # Act
        self.client.force_login(user)
        response = self.client.post(reverse('screening_action'), {'selected_songs': [song1.id, song2.id], 'action': constants.APPROVE_KEYWORD})

        # Assert
        self.assertRedirects(response, reverse('screening_index') + '?filter=pre_screened')
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(1, len(messages))
        self.assertEqual(constants.MESSAGE_ALL_SONGS_MUST_HAVE_UNIQUE_HASH_FOR_BULK_APPROVAL, str(messages[0]))

    def test_cannot_bulk_approve_if_any_song_is_claimed_by_somebody_else(self):
        # Arrange
        user = factories.UserFactory()
        other_user = factories.UserFactory()
        permission = Permission.objects.get(codename='can_approve_songs')
        user.user_permissions.add(permission)

        song1 = song_factories.NewSongFactory(flag=NewSong.Flags.PRE_SCREENED, claimed_by=other_user.profile)
        song2 = song_factories.NewSongFactory(flag=NewSong.Flags.PRE_SCREENED)
        song3 = song_factories.NewSongFactory(flag=NewSong.Flags.PRE_SCREENED)

        # Act
        self.client.force_login(user)
        response = self.client.post(reverse('screening_action'), {'selected_songs': [song1.id, song2.id, song3.id], 'action': constants.APPROVE_KEYWORD})

        # Assert
        self.assertRedirects(response, reverse('screening_index') + '?filter=pre_screened')
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(1, len(messages))
        self.assertEqual(constants.MESSAGE_ALL_SONGS_MUST_NOT_BE_CLAIMED_BY_OTHERS_FOR_BULK_APPROVAL, str(messages[0]))
