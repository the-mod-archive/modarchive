from django.test import TestCase
from django.urls import reverse

from django.contrib.auth.models import Permission
from artists.tests import factories as artist_factories
from interactions.models import Favorite
from interactions.factories import FavoriteFactory
from songs import factories as song_factories
from songs.models import SongStats
from homepage.tests.factories import UserFactory

class AddFavoriteTests(TestCase):
    def test_adds_favorite(self):
        song = song_factories.SongFactory()
        user = UserFactory(permissions=[Permission.objects.get(codename='add_favorite')])
        song_factories.SongStatsFactory(song=song, total_favorites=5)
        self.client.force_login(user)

        # Act
        response = self.client.get(reverse('add_favorite', kwargs = {'pk': song.id}))

        # Assert
        self.assertRedirects(response, reverse('view_song', kwargs = {'pk': song.id}))
        self.assertEqual(
            1,
            Favorite.objects.filter(song_id=song.id, profile_id=user.profile.id).count()
        )
        self.assertEqual(6, SongStats.objects.filter(song=song)[0].total_favorites)

    def test_does_not_add_favorite_when_already_added_as_favorite(self):
        # Arrange
        song = song_factories.SongFactory()
        user = UserFactory(permissions=[Permission.objects.get(codename='add_favorite')])
        self.client.force_login(user)
        FavoriteFactory(profile=user.profile, song=song)

        # Act
        response = self.client.get(reverse('add_favorite', kwargs = {'pk': song.id}))

        # Assert
        self.assertRedirects(response, reverse('view_song', kwargs = {'pk': song.id}))
        self.assertEqual(
            1,
            Favorite.objects.filter(song_id=song.id, profile_id=user.profile.id).count()
        )

    def test_does_not_add_favorite_when_not_authenticated(self):
        # Arrange
        song = song_factories.SongFactory()
        login_url = reverse('login')
        add_favorite_url = reverse('add_favorite', kwargs = {'pk': song.id})

        # Act
        response = self.client.get(add_favorite_url)

        # Assert
        self.assertRedirects(response, f"{login_url}?next={add_favorite_url}")
        self.assertEqual(0, Favorite.objects.filter(song_id=song.id).count())

    def test_does_not_add_artists_own_song_as_favorite(self):
        # Arrange
        user = UserFactory(permissions=[Permission.objects.get(codename='add_favorite')])
        song = song_factories.SongFactory()
        artist_factories.ArtistFactory(user=user, profile=user.profile, songs=(song,))
        self.client.force_login(user)

        # Act
        self.client.get(reverse('add_favorite', kwargs = {'pk': song.id}))

        # Assert
        self.assertEqual(0, Favorite.objects.filter(song_id=song.id).count())

    def test_cannot_add_favorite_without_permission(self):
        # Arrange
        user = UserFactory()
        song = song_factories.SongFactory()
        self.client.force_login(user)

        # Act
        response = self.client.get(reverse('add_favorite', kwargs = {'pk': song.id}))

        # Assert
        self.assertEqual(403, response.status_code)
