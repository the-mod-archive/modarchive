from django.test import TestCase
from django.urls.base import reverse

from songs.models import Song, SongStats

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

class DownloadTests(TestCase):
    fixtures = ["songs.json"]

    def test_download_redirects_to_external_url(self):
        # Arrange
        song = Song.objects.get(pk = 1)

        # Act
        response = self.client.get(f"/songs/{song.id}/download")

        # Assert
        self.assertRedirects(response, f"https://api.modarchive.org/downloads.php?moduleid={song.legacy_id}#{song.filename}", fetch_redirect_response=False)

    def test_download_increases_download_count(self):
        # Arrange
        song = Song.objects.get(pk = 1)
        expected_download_count = song.songstats.downloads + 1

        # Act
        self.client.get(f"/songs/{song.id}/download")
        song.refresh_from_db()

        # Assert
        self.assertEquals(expected_download_count, song.songstats.downloads)

    def test_returns_404_if_song_id_is_missing(self):
        # Act
        response = self.client.get("/songs/1000/download")
        
        # Assert
        self.assertEqual(response.status_code, 404)