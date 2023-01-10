from django.test import TestCase
from django.urls.base import reverse

from artists import factories

class ArtistViewTests(TestCase):
    def test_artist_list_view_contains_all_artists(self):
        # Arrange
        expected_length = 15
        for x in range(expected_length):
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
        self.assertEquals('Arcturus', artist.name)
        self.assertEquals(69117, artist.legacy_id)

    def test_artist_songs_view_contains_specific_artist(self):
        # Arrange
        artist = factories.ArtistFactory(name='Arcturus', legacy_id=69117)
        
        # Act
        response = self.client.get(reverse('view_artist_songs', kwargs = {'pk': artist.id}))

        # Assert
        self.assertTemplateUsed(response, 'artist_songs.html')
        self.assertTrue('artist' in response.context)

        artist = response.context['artist']
        self.assertEquals('Arcturus', artist.name)
        self.assertEquals(69117, artist.legacy_id)

    def test_artist_comments_view_contains_specific_artist(self):
        # Arrange
        artist = factories.ArtistFactory(name='Arcturus', legacy_id=69117)
        
        # Act
        response = self.client.get(reverse('view_artist_comments', kwargs = {'pk': artist.id}))

        # Assert
        self.assertTemplateUsed(response, 'artist_comments.html')
        self.assertTrue('artist' in response.context)

        artist = response.context['artist']
        self.assertEquals('Arcturus', artist.name)
        self.assertEquals(69117, artist.legacy_id)

    def test_artist_favorites_view_contains_specific_artist(self):
        # Arrange
        artist = factories.ArtistFactory(name='Arcturus', legacy_id=69117)
        
        # Act
        response = self.client.get(reverse('view_artist_favorites', kwargs = {'pk': artist.id}))

        # Assert
        self.assertTemplateUsed(response, 'artist_favorites.html')
        self.assertTrue('artist' in response.context)

        artist = response.context['artist']
        self.assertEquals('Arcturus', artist.name)
        self.assertEquals(69117, artist.legacy_id)