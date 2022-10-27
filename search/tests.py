from django.test import TestCase
from django.urls.base import reverse

from artists.models import Artist
from artists import factories as artist_factories
from songs import factories as song_factories
from songs.models import Song

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

class AdvancedSearchTests(TestCase):
    @classmethod
    def setUpTestData(self):
        # Lots of songs
        self.song_visions_it = song_factories.SongFactory(title='Visions', format=Song.Formats.IT, license=Song.Licenses.PUBLIC_DOMAIN)
        self.song_visions_it2 = song_factories.SongFactory(title='Visions of Impulse Tracker', format=Song.Formats.IT)
        self.song_visions_xm = song_factories.SongFactory(title='Visions XM', format=Song.Formats.XM)
        self.song_vision_s3m = song_factories.SongFactory(title='Visions S3M', format=Song.Formats.S3M, license=Song.Licenses.ATTRIBUTION)
        self.song_vision_mod = song_factories.SongFactory(title='Visions MOD', format=Song.Formats.MOD, license=Song.Licenses.PUBLIC_DOMAIN)
        
        super().setUpTestData()

    def test_standard_search_with_no_filters(self):
        # Act
        response = self.client.get(f'{reverse("advanced_search")}?query=visions')

        # Assert
        self.assertEquals(5, len(response.context['search_results']))

    def test_filters_by_format(self):
        # Act
        response = self.client.get(f'{reverse("advanced_search")}?query=visions&format=IT')

        # Assert
        self.assertEquals(2, len(response.context['search_results']))
        self.assertEquals(self.song_visions_it, response.context['search_results'][0])
        self.assertEquals(self.song_visions_it2, response.context['search_results'][1])

    def test_filters_by_multiple_formats(self):
        # Act
        response = self.client.get(f'{reverse("advanced_search")}?query=visions&format=IT&format=XM')

        # Assert
        self.assertEquals(3, len(response.context['search_results']))
        self.assertEquals(self.song_visions_it, response.context['search_results'][0])
        self.assertEquals(self.song_visions_it2, response.context['search_results'][1])
        self.assertEquals(self.song_visions_xm, response.context['search_results'][2])

    def test_filters_by_license(self):
        # Act
        response = self.client.get(f'{reverse("advanced_search")}?query=visions&license=publicdomain')

        # Assert
        self.assertEquals(2, len(response.context['search_results']))
        self.assertEquals(self.song_visions_it, response.context['search_results'][0])
        self.assertEquals(self.song_vision_mod, response.context['search_results'][1])

    def test_filters_by_multiple_licenses(self):
        # Act
        response = self.client.get(f'{reverse("advanced_search")}?query=visions&license=publicdomain&license=by')

        # Assert
        self.assertEquals(3, len(response.context['search_results']))
        self.assertEquals(self.song_visions_it, response.context['search_results'][0])
        self.assertEquals(self.song_vision_s3m, response.context['search_results'][1])
        self.assertEquals(self.song_vision_mod, response.context['search_results'][2])

    def test_mixed_format_and_license_filter(self):
        # Act
        response = self.client.get(f'{reverse("advanced_search")}?query=visions&format=IT&license=publicdomain')

        # Assert
        self.assertEquals(1, len(response.context['search_results']))
        self.assertEquals(self.song_visions_it, response.context['search_results'][0])