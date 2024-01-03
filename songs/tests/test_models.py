from django.test import TestCase

from artists import factories as artist_factories
from homepage.tests import factories
from songs.models import Song
from songs import factories as song_factories


class SongModelTests(TestCase):
    def test_gets_clean_title_when_available(self):
        song = Song(title="song title", clean_title="Song Title")
        self.assertEqual("Song Title", song.get_title())

    def test_gets_original_title_when_no_clean_title_available(self):
        song = Song(title="song title")
        self.assertEqual("song title", song.get_title())

    def test_shows_filename_when_title_is_empty(self):
        song = Song(title="", filename="file.mod")
        self.assertEqual("file.mod", song.get_title())

    def test_shows_filename_when_title_is_whitespace(self):
        song = Song(title="   ", filename="file.mod")
        self.assertEqual("file.mod", song.get_title())

    def test_can_leave_comment_if_not_own_song_and_not_already_commented(self):
        song = Song(id=1, title="song title")
        self.assertTrue(song.can_user_leave_comment(1))

    def test_cannot_leave_comment_if_own_song(self):
        user = factories.UserFactory()
        song = song_factories.SongFactory()
        artist_factories.ArtistFactory(songs=(song,), user=user, profile=user.profile)

        self.assertFalse(song.can_user_leave_comment(user.profile.id))

    def test_cannot_leave_comment_if_already_commented(self):
        user = factories.UserFactory()
        song = song_factories.SongFactory()
        song_factories.CommentFactory(song=song, profile=user.profile)

        self.assertFalse(song.can_user_leave_comment(user.profile.id))

    def test_is_own_song(self):
        user = factories.UserFactory()
        song = song_factories.SongFactory()
        song_2 = song_factories.SongFactory()
        artist_factories.ArtistFactory(songs=(song,), user=user, profile=user.profile)

        self.assertTrue(song.is_own_song(user.profile.id))
        self.assertFalse(song_2.is_own_song(user.profile.id))

    def test_has_artist_commented(self):
        user = factories.UserFactory()
        song = song_factories.SongFactory()
        song_2 = song_factories.SongFactory()
        song_3 = song_factories.SongFactory()
        artist_factories.ArtistFactory(songs=(song, song_2), user=user, profile=user.profile)
        song_factories.ArtistCommentFactory(song=song, profile=user.profile, text="hi")

        self.assertTrue(song.has_artist_commented(user.profile.id))
        self.assertFalse(song_2.has_artist_commented(user.profile.id))
        self.assertFalse(song_3.has_artist_commented(user.profile.id))

    def test_display_file_size(self):
        song = song_factories.SongFactory(file_size=5000)
        song_2 = song_factories.SongFactory(file_size=259871)
        song_3 = song_factories.SongFactory(file_size=2716816)
        self.assertEqual("5000 bytes", song.display_file_size())
        self.assertEqual("259.87 KB", song_2.display_file_size())
        self.assertEqual("2.72 MB", song_3.display_file_size())

    def test_retrieves_stats_correctly(self):
        # Arrange
        song = song_factories.SongFactory()
        song_factories.SongStatsFactory(song=song, downloads=123, total_comments=5, average_comment_score=8.0)

        # Act
        stats = song.get_stats()

        # Assert
        self.assertEqual(123, stats.downloads)
        self.assertEqual(5, stats.total_comments)
        self.assertEqual(8.0, stats.average_comment_score)

    def test_creates_stats_if_not_already_existing(self):
        # Arrange
        song = song_factories.SongFactory()

        # Act
        stats = song.get_stats()

        # Assert
        self.assertEqual(0, stats.downloads)
        self.assertEqual(0, stats.total_comments)
        self.assertEqual(0.0, stats.average_comment_score)

class CommentModelTests(TestCase):
    def test_song_stats_updated_correctly_after_removing_comment(self):
        song = song_factories.SongFactory()
        song_factories.SongStatsFactory(song=song)
        comment_1 = song_factories.CommentFactory(song=song, rating=10)
        song_factories.CommentFactory(song=song, rating=5)

        self.assertEqual(2, song.songstats.total_comments)
        self.assertEqual(7.5, song.songstats.average_comment_score)

        comment_1.delete()

        self.assertEqual(1, song.songstats.total_comments)
        self.assertEqual(5.0, song.songstats.average_comment_score)

    def test_song_stats_updated_correctly_after_removing_final_comment(self):
        song = song_factories.SongFactory()
        song_factories.SongStatsFactory(song=song)
        comment_1 = song_factories.CommentFactory(song=song, rating=10)

        comment_1.delete()

        self.assertEqual(0, song.songstats.total_comments)
        self.assertEqual(0.0, song.songstats.average_comment_score)
        