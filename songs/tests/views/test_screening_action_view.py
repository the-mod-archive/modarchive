from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls.base import reverse

from homepage.tests import factories
from songs import factories as song_factories
from songs.models import NewSong

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
        self.assertRedirects(response, reverse('screening_index'))

    def test_screener_can_claim_single_unclaimed_song(self):
        # Arrange
        user = factories.UserFactory()
        permission = Permission.objects.get(codename='can_approve_songs')
        user.user_permissions.add(permission)
        song1 = song_factories.NewSongFactory(filename='song1.mod')

        # Act
        self.client.force_login(user)
        response = self.client.post(reverse('screening_action'), {'selected_songs': [song1.id], 'action': 'claim'})

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
        song1 = song_factories.NewSongFactory(filename='song1.mod')
        song2 = song_factories.NewSongFactory(filename='song2.mod')

        # Act
        self.client.force_login(user)
        response = self.client.post(reverse('screening_action'), {'selected_songs': [song1.id, song2.id], 'action': 'claim'})

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
        song1 = song_factories.NewSongFactory(filename='song1.mod', claimed_by=other_user.profile)
        song2 = song_factories.NewSongFactory(filename='song2.mod', claimed_by=other_user.profile)

        # Act
        self.client.force_login(user)
        response = self.client.post(reverse('screening_action'), {'selected_songs': [song1.id, song2.id], 'action': 'claim'})

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
        song1 = song_factories.NewSongFactory(filename='song1.mod', claimed_by=user.profile)
        song2 = song_factories.NewSongFactory(filename='song2.mod', claimed_by=user.profile)

        # Act
        self.client.force_login(user)
        response = self.client.post(reverse('screening_action'), {'selected_songs': [song1.id, song2.id], 'action': 'pre_screen'})

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

    def test_cannot_prescreen_unclaimed_songs(self):
        # Arrange
        user = factories.UserFactory()
        permission = Permission.objects.get(codename='can_approve_songs')
        user.user_permissions.add(permission)
        song1 = song_factories.NewSongFactory(filename='song1.mod')
        song2 = song_factories.NewSongFactory(filename='song2.mod')

        # Act
        self.client.force_login(user)
        response = self.client.post(reverse('screening_action'), {'selected_songs': [song1.id, song2.id], 'action': 'pre_screen'})

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
        song1 = song_factories.NewSongFactory(filename='song1.mod', claimed_by=other_user.profile)
        song2 = song_factories.NewSongFactory(filename='song2.mod', claimed_by=other_user.profile)

        # Act
        self.client.force_login(user)
        response = self.client.post(reverse('screening_action'), {'selected_songs': [song1.id, song2.id], 'action': 'pre_screen'})

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
        song1 = song_factories.NewSongFactory(filename='song1.mod', claimed_by=user.profile)
        song2 = song_factories.NewSongFactory(filename='song2.mod', claimed_by=user.profile)

        # Act
        self.client.force_login(user)
        response = self.client.post(reverse('screening_action'), {'selected_songs': [song1.id, song2.id], 'action': 'pre_screen_and_recommend'})

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

    def test_cannot_prescreen_and_recommend_unclaimed_songs(self):
        # Arrange
        user = factories.UserFactory()
        permission = Permission.objects.get(codename='can_approve_songs')
        user.user_permissions.add(permission)
        song1 = song_factories.NewSongFactory(filename='song1.mod')
        song2 = song_factories.NewSongFactory(filename='song2.mod')

        # Act
        self.client.force_login(user)
        response = self.client.post(reverse('screening_action'), {'selected_songs': [song1.id, song2.id], 'action': 'pre_screen_and_recommend'})

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
        song1 = song_factories.NewSongFactory(filename='song1.mod', claimed_by=other_user.profile)
        song2 = song_factories.NewSongFactory(filename='song2.mod', claimed_by=other_user.profile)

        # Act
        self.client.force_login(user)
        response = self.client.post(reverse('screening_action'), {'selected_songs': [song1.id, song2.id], 'action': 'pre_screen_and_recommend'})

        # Assert
        self.assertRedirects(response, reverse('screening_index'))
        song1.refresh_from_db()
        song2.refresh_from_db()
        self.assertEqual(other_user.profile, song1.claimed_by)
        self.assertEqual(other_user.profile, song2.claimed_by)
        self.assertIsNone(song1.flag)
        self.assertIsNone(song2.flag)
