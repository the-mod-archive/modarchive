from django.test import TestCase
from django.urls.base import reverse

from artists.models import Artist
from artists import factories as artist_factories
from songs import factories as song_factories

class SignalsTests(TestCase):
    def test_song_save_creates_search_vectors(self):
        song = song_factories.SongFactory(title='Some Song', comment_text='This is my comment text', instrument_text='This is my instrument text')
        song.refresh_from_db()

        self.assertTrue(song.title_vector)
        self.assertTrue(song.comment_text_vector)
        self.assertTrue(song.instrument_text_vector)

    def test_artist_save_creates_search_vectors(self):
        artist = artist_factories.ArtistFactory(name="Artistguy")
        artist.refresh_from_db()
        self.assertTrue(artist.search_document)

class QuickSearchTests(TestCase):
    @classmethod
    def setUpTestData(self):
        # Lots of songs
        self.song_visions = song_factories.SongFactory(title='Visions')
        self.song_visions_of_oblivion = song_factories.SongFactory(title='Visions of Oblivion')
        self.song_untitled = song_factories.SongFactory(title='untitled')
        self.song_last_day = song_factories.SongFactory(title='-=the last day=-')
        self.song_teknotrash = song_factories.SongFactory(title='teknotrash 1.0')
        self.song_neverland = song_factories.SongFactory(title='neverland')
        self.song_pestilence = song_factories.SongFactory(title='pestilence')
        self.song_in_chains = song_factories.SongFactory(title='In Chains')
        self.song_cjerra = song_factories.SongFactory(title='-==- Cjerra -==-')
        self.song_crack_2000 = song_factories.SongFactory(title='Crack 2000')
        self.song_pfannekuchen = song_factories.SongFactory(title='pfannekuchen etc. :P')
        self.song_dirty_harry = song_factories.SongFactory(title='^^^ DIRTY HARRY ^^^')
        song_factories.SongFactory(title='unknown parts of the universe')
        song_factories.SongFactory(title='willy universe')
        song_factories.SongFactory(title='++the hunter++')
        song_factories.SongFactory(title='Atomic 2 theme')
        song_factories.SongFactory(title='Before dark')
        song_factories.SongFactory(title='doubt[stereomix]')
        self.song_outcast = song_factories.SongFactory(title='Unclean', clean_title='Outcast')
        self.song_subliminal_messages = song_factories.SongFactory(title='Subliminal Messages')
        
        # 3 artists
        self.artist_subliminal = artist_factories.ArtistFactory(name="Subliminal", songs=[self.song_cjerra, self.song_crack_2000, self.song_pfannekuchen, self.song_dirty_harry])
        self.artist_wurkir = artist_factories.ArtistFactory(name="Wurkir", songs=[self.song_teknotrash, self.song_neverland, self.song_pestilence, self.song_in_chains, self.song_visions_of_oblivion])
        artist_factories.ArtistFactory(name="Kalanaras", songs=[self.song_visions, self.song_untitled, self.song_last_day])
        super().setUpTestData()

    def test_quick_search_retrieves_matching_songs_and_artists(self):        
        # Act
        response = self.client.get('/search/?query=subliminal&songs=on&artists=on')

        # Assert
        self.assertEquals(2, len(response.context['search_results']))
        items = list(map(lambda x: x['item'], response.context['search_results']))
        self.assertTrue(self.artist_subliminal in items)
        self.assertTrue(self.song_subliminal_messages in items)

    def test_quick_search_gets_matching_songs(self):
        # Act
        response = self.client.get('/search/?query=visions&songs=on&artists=on')

        # Assert
        self.assertEquals(2, len(response.context['search_results']))
        items = list(map(lambda x: x['item'], response.context['search_results']))
        self.assertTrue(self.song_visions in items)
        self.assertTrue(self.song_visions_of_oblivion in items)

    def test_quick_search_gets_matching_artists(self):
        # Act
        response = self.client.get('/search/?query=wurkir&songs=on&artists=on')

        # Assert
        self.assertEquals(1, len(response.context['search_results']))
        self.assertEquals(self.artist_wurkir, response.context['search_results'][0]['item'])

    def test_quick_search_gets_song_by_clean_title(self):
        # Act
        response = self.client.get('/search/?query=outcast&songs=on&artists=on')

        # Assert
        self.assertEquals(1, len(response.context['search_results']))
        self.assertEquals(self.song_outcast, response.context['search_results'][0]['item'])

    def test_quick_search_does_not_search_title_when_clean_title_is_set(self):
        # Act
        response = self.client.get('/search/?query=unclean&songs=on&artists=on')

        # Assert
        self.assertEquals(0, len(response.context['search_results']))