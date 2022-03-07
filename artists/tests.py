from django.test import TestCase
from django.urls.base import reverse

class ArtistViewTests(TestCase):
    fixtures = ["artists.json", "songs.json"]

    def test_artist_list_view_contains_all_artists(self):
        # Arrange
        expected_length = 15
        
        # Act
        response = self.client.get(reverse('artists'))
        
        # Assert
        actual_length = len(response.context['object_list'])
        
        self.assertTemplateUsed(response, 'artist_list.html')
        self.assertTrue('object_list' in response.context)
        self.assertEqual(expected_length, actual_length, f"Expected {expected_length} objects in artists list but got {actual_length}")

    def test_artist_view_contains_specific_artist(self):
        # Act
        response = self.client.get(reverse('view_artist', kwargs = {'key': 'Arcturus'}))

        # Assert
        self.assertTemplateUsed(response, 'artist.html')
        self.assertTrue('artist' in response.context)

        artist = response.context['artist']
        self.assertEquals('Arcturus', artist.name)
        self.assertEquals(69117, artist.legacy_id)