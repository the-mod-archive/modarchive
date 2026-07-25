from django.test import TestCase

from songs.factories import SongFactory
from interactions.factories import CommentFactory

class CommentModelTests(TestCase):
    # These tests are to make sure that signals are automatically updating the song stats when comments are added or removed
    def test_song_stats_updated_correctly_after_removing_comment(self):
        song = SongFactory()

        comment_1 = CommentFactory(song=song, rating=10)
        CommentFactory(song=song, rating=5)

        self.assertEqual(2, song.comments_count)
        self.assertEqual(7.5, song.average_rating)

        comment_1.delete()

        self.assertEqual(1, song.comments_count)
        self.assertEqual(5.0, song.average_rating)

    def test_song_stats_updated_correctly_after_removing_final_comment(self):
        song = SongFactory()
        comment_1 = CommentFactory(song=song, rating=10)

        comment_1.delete()

        self.assertEqual(0, song.comments_count)
        self.assertEqual(None, song.average_rating)
