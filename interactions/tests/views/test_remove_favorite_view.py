from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import Permission
from interactions.models import Favorite
from interactions.factories import FavoriteFactory
from songs.factories import SongFactory
from homepage.tests.factories import UserFactory

class RemoveFavoriteTests(TestCase):
    def test_removes_favorite(self):
        # Arrange
        song = SongFactory(favorites_count=5)
        user = UserFactory(permissions=[Permission.objects.get(codename='delete_favorite')])
        self.client.force_login(user)
        FavoriteFactory(profile=user.profile, song=song)

        # Act
        response = self.client.get(reverse('remove_favorite', kwargs = {'pk': song.id}))

        # Assert
        self.assertRedirects(response, reverse('view_song', kwargs = {'pk': song.id}))
        self.assertEqual(
            0,
            Favorite.objects.filter(song_id=song.id, profile_id=user.profile.id).count()
        )
        song.refresh_from_db()
        self.assertEqual(4, song.favorites_count)

    def test_does_not_remove_favorite_when_not_already_added_as_favorite(self):
        # Arrange
        song = SongFactory()
        user = UserFactory(permissions=[Permission.objects.get(codename='delete_favorite')])
        self.client.force_login(user)

        # Act
        response = self.client.get(reverse('remove_favorite', kwargs = {'pk': song.id}))

        # Assert
        self.assertRedirects(response, reverse('view_song', kwargs = {'pk': song.id}))
        self.assertEqual(
            0,
            Favorite.objects.filter(song_id=song.id, profile_id=user.profile.id).count()
        )

    def test_does_not_remove_favorite_when_not_authenticated(self):
        # Arrange
        song = SongFactory()
        user = UserFactory(permissions=[Permission.objects.get(codename='delete_favorite')])
        login_url = reverse('login')
        remove_favorite_url = reverse('remove_favorite', kwargs = {'pk': song.id})
        FavoriteFactory(profile=user.profile, song=song)

        # Act
        response = self.client.get(remove_favorite_url)

        # Assert
        self.assertRedirects(response, f"{login_url}?next={remove_favorite_url}")
        self.assertEqual(1, Favorite.objects.filter(song_id=song.id).count())

    def test_cannot_remove_favorite_without_permission(self):
        # Arrange
        song = SongFactory(favorites_count=5)
        user = UserFactory()
        self.client.force_login(user)
        FavoriteFactory(profile=user.profile, song=song)

        # Act
        response = self.client.get(reverse('remove_favorite', kwargs = {'pk': song.id}))

        # Assert
        self.assertEqual(403, response.status_code)
