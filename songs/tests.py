from django.test import TestCase
from django.urls.base import reverse

from songs.models import Song

class SongTests(TestCase):
    def test_gets_clean_title_when_available(self):
        song = Song(title="song title", clean_title="Song Title")
        self.assertEqual("Song Title", song.get_title())

    def test_gets_original_title_when_no_clean_title_available(self):
        song = Song(title="song title")
        self.assertEqual("song title", song.get_title())

class SongViewTests(TestCase):
    fixtures = ["songs.json"]

    def test_song_list_view_contains_all_songs(self):
        # Arrange
        expected_length = 33
        
        # Act
        response = self.client.get(reverse('songs'))
        
        # Assert
        actual_length = len(response.context['object_list'])
        
        self.assertTemplateUsed(response, 'song_list.html')
        self.assertTrue('object_list' in response.context)
        self.assertEqual(expected_length, actual_length, f"Expected {expected_length} objects in songs list but got {actual_length}")

    def test_song_view_contains_specific_song(self):
        # Act
        response = self.client.get(reverse('view_song', kwargs = {'pk': 1}))

        # Assert
        self.assertTemplateUsed(response, 'song.html')
        self.assertTrue('song' in response.context)

        song = response.context['song']
        self.assertEquals('Tangerine Fascination', song.get_title())
        self.assertEquals(48552, song.legacy_id)