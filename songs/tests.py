from turtle import title
from django.test import TestCase

from songs.models import Song

class SongTests(TestCase):
    def test_gets_clean_title_when_available(self):
        song = Song(title="song title", clean_title="Song Title")
        self.assertEqual("Song Title", song.get_title())

    def test_gets_original_title_when_no_clean_title_available(self):
        song = Song(title="song title")
        self.assertEqual("song title", song.get_title())