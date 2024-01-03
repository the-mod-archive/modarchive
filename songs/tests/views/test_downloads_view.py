from django.test import TestCase

from songs import factories as song_factories

class DownloadTests(TestCase):
    def test_download_redirects_to_external_url(self):
        # Arrange
        song = song_factories.SongFactory(legacy_id=12345)
        song_factories.SongStatsFactory(song=song)

        # Act
        response = self.client.get(f"/songs/{song.id}/download")

        # Assert
        self.assertRedirects(response, f"https://api.modarchive.org/downloads.php?moduleid={song.legacy_id}#{song.filename}", fetch_redirect_response=False)

    def test_download_increases_download_count(self):
        # Arrange
        song = song_factories.SongFactory(legacy_id=12345)
        stats = song_factories.SongStatsFactory(song=song, downloads=100)

        # Act
        self.client.get(f"/songs/{song.id}/download")
        song.refresh_from_db()

        # Assert
        self.assertEqual(stats.downloads + 1, song.songstats.downloads)

    def test_returns_404_if_song_id_is_missing(self):
        # Act
        response = self.client.get("/songs/1000/download")
        
        # Assert
        self.assertEqual(response.status_code, 404)