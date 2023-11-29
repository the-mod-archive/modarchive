from django.test import TestCase
from django.urls.base import reverse

from artists import factories
from songs import factories as song_factories
from homepage.tests import factories as homepage_factories

class ArtistViewTests(TestCase):
    def test_artist_list_view_contains_all_artists(self):
        # Arrange
        expected_length = 15
        for _ in range(expected_length):
            factories.ArtistFactory()
        
        # Act
        response = self.client.get(reverse('artists'))
        
        # Assert
        actual_length = len(response.context['object_list'])
        self.assertEqual(expected_length, actual_length, f"Expected {expected_length} objects in artists list but got {actual_length}")
        self.assertTemplateUsed(response, 'artist_list.html')

    def test_artist_view_contains_specific_artist(self):
        # Arrange
        artist = factories.ArtistFactory(name='Arcturus', legacy_id=69117)
        
        # Act
        response = self.client.get(reverse('view_artist', kwargs = {'pk': artist.id}))

        # Assert
        self.assertTemplateUsed(response, 'artist_overview.html')
        self.assertTrue('artist' in response.context)

        artist = response.context['artist']
        self.assertEqual('Arcturus', artist.name)
        self.assertEqual(69117, artist.legacy_id)

    def test_artist_songs_view_contains_specific_artist(self):
        # Arrange
        artist = factories.ArtistFactory(name='Arcturus', legacy_id=69117)
        
        # Act
        response = self.client.get(reverse('view_artist_songs', kwargs = {'pk': artist.id}))

        # Assert
        self.assertTemplateUsed(response, 'artist_songs.html')
        self.assertTrue('artist' in response.context)

        artist = response.context['artist']
        self.assertEqual('Arcturus', artist.name)
        self.assertEqual(69117, artist.legacy_id)

    def test_artist_comments_view_contains_specific_artist(self):
        # Arrange
        user = homepage_factories.UserFactory()
        artist = factories.ArtistFactory(name='Arcturus', legacy_id=69117, user=user, profile=user.profile)
        
        # Act
        response = self.client.get(reverse('view_artist_comments', kwargs = {'pk': artist.id}))

        # Assert
        self.assertTemplateUsed(response, 'artist_comments.html')
        self.assertTrue('artist' in response.context)

        artist = response.context['artist']
        self.assertEqual('Arcturus', artist.name)
        self.assertEqual(69117, artist.legacy_id)

    def test_artist_favorites_view_contains_specific_artist(self):
        # Arrange
        user = homepage_factories.UserFactory()
        artist = factories.ArtistFactory(name='Arcturus', legacy_id=69117, user=user, profile=user.profile)
        
        # Act
        response = self.client.get(reverse('view_artist_favorites', kwargs = {'pk': artist.id}))

        # Assert
        self.assertTemplateUsed(response, 'artist_favorites.html')
        self.assertTrue('artist' in response.context)

        artist = response.context['artist']
        self.assertEqual('Arcturus', artist.name)
        self.assertEqual(69117, artist.legacy_id)

class ArtistSongViewTests(TestCase):
    def test_artist_song_view_contains_songs(self):
        # Arrange
        songs = [song_factories.SongFactory() for _ in range(10)]
        
        artist = factories.ArtistFactory(name='Arcturus', songs=songs)

        # Act
        response = self.client.get(reverse('view_artist_songs', kwargs = {'pk': artist.pk}))

        # Assert
        self.assertEqual(10, len(response.context['songs']))

    def test_artist_song_view_contains_first_page_of_songs(self):
        # Arrange
        songs = [song_factories.SongFactory() for _ in range(30)]
        
        artist = factories.ArtistFactory(name='Arcturus', songs=songs)

        # Act
        response = self.client.get(reverse('view_artist_songs', kwargs = {'pk': artist.pk}))

        # Assert
        self.assertEqual(25, len(response.context['songs']))

    def test_artist_song_view_contains_second_page_of_songs(self):
        # Arrange
        songs = [song_factories.SongFactory() for _ in range(30)]
        
        artist = factories.ArtistFactory(name='Arcturus', songs=songs)

        # Act
        response = self.client.get(reverse('view_artist_songs', kwargs = {'pk': artist.pk}) + "?page=2")

        # Assert
        self.assertEqual(5, len(response.context['songs']))