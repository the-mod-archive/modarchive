from django.test import TestCase

from songs import factories as song_factories

class DownloadTests(TestCase):
    def test_download_redirects_to_external_url(self):
        # Arrange
        song = song_factories.SongFactory(legacy_id=12345)

        # Act
        response = self.client.get(f"/songs/{song.id}/download")

        # Assert
        self.assertRedirects(response, f"https://api.modarchive.org/downloads.php?moduleid={song.legacy_id}#{song.filename}", fetch_redirect_response=False)

    def test_download_increases_download_count(self):
        # Arrange
        song = song_factories.SongFactory(legacy_id=12345, downloads_count=100)

        # Act
        self.client.get(f"/songs/{song.id}/download")
        song.refresh_from_db()

        # Assert
        self.assertEqual(101, song.downloads_count)

    def test_returns_404_if_song_id_is_missing(self):
        # Act
        response = self.client.get("/songs/1000/download")
        
        # Assert
        self.assertEqual(response.status_code, 404)