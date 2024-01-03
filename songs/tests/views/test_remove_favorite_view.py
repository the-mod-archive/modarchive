from django.test import TestCase
from django.urls import reverse

from songs import factories as song_factories
from songs.models import SongStats, Favorite
from homepage.tests import factories

class RemoveFavoriteTests(TestCase):
    def test_removes_favorite(self):
        # Arrange
        song = song_factories.SongFactory()
        song_factories.SongStatsFactory(song=song, total_favorites=5)
        user = factories.UserFactory()
        self.client.force_login(user)
        song_factories.FavoriteFactory(profile=user.profile, song=song)

        # Act
        response = self.client.get(reverse('remove_favorite', kwargs = {'pk': song.id}))

        # Assert
        self.assertRedirects(response, reverse('view_song', kwargs = {'pk': song.id}))
        self.assertEqual(
            0,
            Favorite.objects.filter(song_id=song.id, profile_id=user.profile.id).count()
        )
        self.assertEqual(4, SongStats.objects.filter(song=song)[0].total_favorites)

    def test_does_not_remove_favorite_when_not_already_added_as_favorite(self):
        # Arrange
        song = song_factories.SongFactory()
        user = factories.UserFactory()
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
        song = song_factories.SongFactory()
        user = factories.UserFactory()
        login_url = reverse('login')
        remove_favorite_url = reverse('remove_favorite', kwargs = {'pk': song.id})
        song_factories.FavoriteFactory(profile=user.profile, song=song)

        # Act
        response = self.client.get(remove_favorite_url)

        # Assert
        self.assertRedirects(response, f"{login_url}?next={remove_favorite_url}")
        self.assertEqual(1, Favorite.objects.filter(song_id=song.id).count())
