import os
from datetime import date

from django.test import TestCase
from django.urls.base import reverse
from django.contrib.auth.models import Permission
from django.contrib.messages import get_messages
from django.conf import settings

from homepage.tests import factories
from uploads import factories as upload_factories
from uploads import constants
from uploads.models import NewSong, RejectedSong

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
        song = upload_factories.NewSongFactory(claimed_by=user.profile)

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
        song = upload_factories.NewSongFactory(claimed_by=None)
        song_2 = upload_factories.NewSongFactory(claimed_by=self.user.profile)

        # Act
        response = self.client.get(f"{reverse('screening_reject')}?song_ids={song.id},{song_2.id}")

        # Assert
        self.assertRedirects(response, reverse('screening_index'))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(1, len(messages))
        self.assertEqual(constants.REJECTION_ALL_SONGS_MUST_BE_CLAIMED, str(messages[0]))

    def test_renders_template_if_all_songs_are_claimed(self):
        # Arrange
        song = upload_factories.NewSongFactory(claimed_by=self.user.profile)
        song_2 = upload_factories.NewSongFactory(claimed_by=self.user.profile)

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
        song = upload_factories.NewSongFactory(claimed_by=None)
        song_2 = upload_factories.NewSongFactory(claimed_by=self.user.profile)

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

class FinalizeRejectionTests(TestCase):
    new_file_dir = settings.NEW_FILE_DIR
    rejected_file_dir = settings.REJECTED_FILE_DIR

    def setUp(self):
        self.user = factories.UserFactory()
        permission = Permission.objects.get(codename='can_approve_songs')
        self.user.user_permissions.add(permission)
        self.client.force_login(self.user)

    def tearDown(self):
        # Cleanup new_file_dir after each test
        for filename in os.listdir(self.new_file_dir):
            file_path = os.path.join(self.new_file_dir, filename)
            os.remove(file_path)

        for filename in os.listdir(self.rejected_file_dir):
            file_path = os.path.join(self.rejected_file_dir, filename)
            os.remove(file_path)

    def create_song(self, hash_code='123'):
        song = upload_factories.NewSongFactory(claimed_by=self.user.profile, hash=hash_code)
        # Create a dummy file to represent the uploaded file
        with open(f'{self.new_file_dir}/{song.filename}.zip', 'w', encoding='utf-8') as file:
            file.write('test')
        return song

    def assert_song(self, song, rejected_song, reason, is_temporary, message):
        self.assertFalse(NewSong.objects.filter(id=song.id).exists())
        self.assertEqual(rejected_song.rejected_by, self.user.profile)
        self.assertEqual(rejected_song.reason, reason)
        self.assertEqual(rejected_song.is_temporary, is_temporary)
        self.assertEqual(rejected_song.message, message)
        self.assertEqual(rejected_song.filename, song.filename)
        previous_location = f'{self.new_file_dir}/{song.filename}.zip'
        self.assertFalse(os.path.exists(previous_location))
        today = date.today().strftime('%Y%m%d')
        new_location = f'{settings.REJECTED_FILE_DIR}/{today}-{song.filename}.zip'
        self.assertTrue(os.path.exists(new_location))

    def test_rejecting_a_song_removes_it_from_the_screening_queue(self):
        # Arrange
        song = self.create_song()

        # Act
        response = self.client.post(
            reverse('screening_reject'),
            data={'song_ids': song.id, 'is_temporary': False, 'rejection_reason': RejectedSong.Reasons.ALREADY_EXISTS}
        )

        # Assert
        self.assertRedirects(response, reverse('screening_index'), target_status_code=200)
        self.assert_song(song, RejectedSong.objects.get(hash=song.hash), RejectedSong.Reasons.ALREADY_EXISTS, False, '')

    def test_rejecting_multiple_songs_removes_them_from_screening_queue(self):
        # Arrange
        song = self.create_song()
        song_2 = self.create_song(hash_code='456')
        message = 'test message'

        # Act
        response = self.client.post(
            reverse('screening_reject'),
            data={
                'song_ids': f"{song.id},{song_2.id}",
                'is_temporary': True,
                'rejection_reason': RejectedSong.Reasons.POOR_QUALITY,
                'message': message
            }
        )

        # Assert
        self.assertRedirects(response, reverse('screening_index'), target_status_code=200)
        self.assert_song(song, RejectedSong.objects.get(hash=song.hash), RejectedSong.Reasons.POOR_QUALITY, True, message)
        self.assert_song(song_2, RejectedSong.objects.get(hash=song_2.hash), RejectedSong.Reasons.POOR_QUALITY, True, message)
