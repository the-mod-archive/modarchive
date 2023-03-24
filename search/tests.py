import random

from django.test import TestCase
from django.urls.base import reverse

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
        self.song_visions_it = song_factories.SongFactory(title='Visions', format=Song.Formats.IT, license=Song.Licenses.PUBLIC_DOMAIN, file_size=10000000, comment_text="flerp")
        self.song_visions_it2 = song_factories.SongFactory(title='Visions of Impulse Tracker', format=Song.Formats.IT, genre=Song.Genres.ALTERNATIVE, comment_text="flerp", instrument_text="flerp")
        self.song_visions_xm = song_factories.SongFactory(title='Visions XM', format=Song.Formats.XM, genre=Song.Genres.ALTERNATIVE_GOTHIC, instrument_text="flerp")
        self.song_visions_s3m = song_factories.SongFactory(title='Visions S3M', format=Song.Formats.S3M, license=Song.Licenses.ATTRIBUTION, channels=8, filename="blerp1.s3m")
        self.song_visions_mod = song_factories.SongFactory(title='Visions MOD', format=Song.Formats.MOD, license=Song.Licenses.PUBLIC_DOMAIN, genre=Song.Genres.ALTERNATIVE, file_size=5000, channels=4, filename="blerp2.mod")
        self.song_flerp = song_factories.SongFactory(title="Flerp", format=Song.Formats.MTM)
        self.song_flerp_filename = song_factories.SongFactory(title="Untitled", format=Song.Formats.MOD, filename="flerp.mod")
        
        super().setUpTestData()

    def test_standard_search_with_no_filters(self):
        # Act
        response = self.client.get(f'{reverse("advanced_search")}?query=visions&type=title')

        # Assert
        self.assertEquals(5, len(response.context['search_results']))

    def test_filters_by_format(self):
        # Act
        response = self.client.get(f'{reverse("advanced_search")}?query=visions&format=IT&type=title')

        # Assert
        self.assertEquals(2, len(response.context['search_results']))
        self.assertEquals(self.song_visions_it, response.context['search_results'][0])
        self.assertEquals(self.song_visions_it2, response.context['search_results'][1])

    def test_filters_by_multiple_formats(self):
        # Act
        response = self.client.get(f'{reverse("advanced_search")}?query=visions&format=IT&format=XM&type=title')

        # Assert
        self.assertEquals(3, len(response.context['search_results']))
        self.assertEquals(self.song_visions_it, response.context['search_results'][0])
        self.assertEquals(self.song_visions_it2, response.context['search_results'][1])
        self.assertEquals(self.song_visions_xm, response.context['search_results'][2])

    def test_filters_by_license(self):
        # Act
        response = self.client.get(f'{reverse("advanced_search")}?query=visions&license=publicdomain&type=title')

        # Assert
        self.assertEquals(2, len(response.context['search_results']))
        self.assertEquals(self.song_visions_it, response.context['search_results'][0])
        self.assertEquals(self.song_visions_mod, response.context['search_results'][1])

    def test_filters_by_multiple_licenses(self):
        # Act
        response = self.client.get(f'{reverse("advanced_search")}?query=visions&license=publicdomain&license=by&type=title')

        # Assert
        self.assertEquals(3, len(response.context['search_results']))
        self.assertEquals(self.song_visions_it, response.context['search_results'][0])
        self.assertEquals(self.song_visions_s3m, response.context['search_results'][1])
        self.assertEquals(self.song_visions_mod, response.context['search_results'][2])

    def test_mixed_format_and_license_filter(self):
        # Act
        response = self.client.get(f'{reverse("advanced_search")}?query=visions&format=IT&license=publicdomain&type=title')

        # Assert
        self.assertEquals(1, len(response.context['search_results']))
        self.assertEquals(self.song_visions_it, response.context['search_results'][0])

    def test_filters_by_genre(self):
        # Act
        response = self.client.get(f'{reverse("advanced_search")}?query=visions&genre={Song.Genres.ALTERNATIVE}&type=title')

        # Assert
        self.assertEquals(2, len(response.context['search_results']))
        self.assertEquals(self.song_visions_it2, response.context['search_results'][0])
        self.assertEquals(self.song_visions_mod, response.context['search_results'][1])

    def test_filters_by_multiple_genres(self):
        # Act
        response = self.client.get(f'{reverse("advanced_search")}?query=visions&genre={Song.Genres.ALTERNATIVE}&genre={Song.Genres.ALTERNATIVE_GOTHIC}&type=title')

        # Assert
        self.assertEquals(3, len(response.context['search_results']))
        self.assertEquals(self.song_visions_it2, response.context['search_results'][0])
        self.assertEquals(self.song_visions_xm, response.context['search_results'][1])
        self.assertEquals(self.song_visions_mod, response.context['search_results'][2])

    def test_filters_by_minimum_file_size(self):
        # Act
        response = self.client.get(f'{reverse("advanced_search")}?query=visions&minSize=10000&type=title')

        # Assert
        self.assertEquals(4, len(response.context['search_results']))
        self.assertEquals(self.song_visions_it, response.context['search_results'][0])
        self.assertEquals(self.song_visions_it2, response.context['search_results'][1])
        self.assertEquals(self.song_visions_xm, response.context['search_results'][2])
        self.assertEquals(self.song_visions_s3m, response.context['search_results'][3])

    def test_filters_by_maximum_file_size(self):
        # Act
        response = self.client.get(f'{reverse("advanced_search")}?query=visions&maxSize=200000&type=title')

        # Assert
        self.assertEquals(4, len(response.context['search_results']))
        self.assertEquals(self.song_visions_it2, response.context['search_results'][0])
        self.assertEquals(self.song_visions_xm, response.context['search_results'][1])
        self.assertEquals(self.song_visions_s3m, response.context['search_results'][2])
        self.assertEquals(self.song_visions_mod, response.context['search_results'][3])

    def test_filters_by_minimum_and_maximum_file_size(self):
        # Act
        response = self.client.get(f'{reverse("advanced_search")}?query=visions&minSize=10000&maxSize=200000&type=title')

        # Assert
        self.assertEquals(3, len(response.context['search_results']))
        self.assertEquals(self.song_visions_it2, response.context['search_results'][0])
        self.assertEquals(self.song_visions_xm, response.context['search_results'][1])
        self.assertEquals(self.song_visions_s3m, response.context['search_results'][2])

    def test_filters_by_minimum_channels(self):
        # Act
        response = self.client.get(f'{reverse("advanced_search")}?query=visions&minChannels=8&type=title')

        # Assert
        self.assertEquals(4, len(response.context['search_results']))
        self.assertEquals(self.song_visions_it, response.context['search_results'][0])
        self.assertEquals(self.song_visions_it2, response.context['search_results'][1])
        self.assertEquals(self.song_visions_xm, response.context['search_results'][2])
        self.assertEquals(self.song_visions_s3m, response.context['search_results'][3])

    def test_filters_by_maximum_channels(self):
        # Act
        response = self.client.get(f'{reverse("advanced_search")}?query=visions&maxChannels=8&type=title')

        # Assert
        self.assertEquals(2, len(response.context['search_results']))
        self.assertEquals(self.song_visions_s3m, response.context['search_results'][0])
        self.assertEquals(self.song_visions_mod, response.context['search_results'][1])

    def test_filters_by_minimum_and_maximum_channels(self):
        # Act
        response = self.client.get(f'{reverse("advanced_search")}?query=visions&minChannels=6&maxChannels=10&type=title')

        # Assert
        self.assertEquals(1, len(response.context['search_results']))
        self.assertEquals(self.song_visions_s3m, response.context['search_results'][0])

    def test_minimum_file_size_cannot_be_negative(self):
        # Act
        response = self.client.get(f'{reverse("advanced_search")}?query=visions&minSize=-1000&type=title')

        # Assert
        self.assertEquals(1, len(response.context['form'].errors))
        self.assertEquals(1, len(response.context['form'].errors['minSize']))
        self.assertEquals('Ensure this value is greater than or equal to 0.', response.context['form'].errors['minSize'][0])

    def test_maximum_file_size_cannot_be_negative(self):
        # Act
        response = self.client.get(f'{reverse("advanced_search")}?query=visions&maxSize=-1000&type=title')

        # Assert
        self.assertEquals(1, len(response.context['form'].errors))
        self.assertEquals(1, len(response.context['form'].errors['maxSize']))
        self.assertEquals('Ensure this value is greater than or equal to 0.', response.context['form'].errors['maxSize'][0])

    def test_minimum_channels_cannot_be_negative(self):
        # Act
        response = self.client.get(f'{reverse("advanced_search")}?query=visions&minChannels=-1&type=title')

        # Assert
        self.assertEquals(1, len(response.context['form'].errors))
        self.assertEquals(1, len(response.context['form'].errors['minChannels']))
        self.assertEquals('Ensure this value is greater than or equal to 1.', response.context['form'].errors['minChannels'][0])

    def test_maximum_channels_cannot_be_negative(self):
        # Act
        response = self.client.get(f'{reverse("advanced_search")}?query=visions&maxChannels=-1&type=title')

        # Assert
        self.assertEquals(1, len(response.context['form'].errors))
        self.assertEquals(1, len(response.context['form'].errors['maxChannels']))
        self.assertEquals('Ensure this value is greater than or equal to 1.', response.context['form'].errors['maxChannels'][0])

    def test_max_size_cannot_be_lower_than_min_size(self):
        # Act
        response = self.client.get(f'{reverse("advanced_search")}?query=visions&minSize=10000&maxSize=5000&type=title')

        # Assert
        self.assertEquals(1, len(response.context['form'].errors))
        self.assertEquals(1, len(response.context['form'].errors['__all__']))
        self.assertEquals('Minimum size must be less than or equal to maximum size.', response.context['form'].errors['__all__'][0])

    def test_max_channels_cannot_be_lower_than_min_channels(self):
        # Act
        response = self.client.get(f'{reverse("advanced_search")}?query=visions&minChannels=4&maxChannels=2&type=title')

        # Assert
        self.assertEquals(1, len(response.context['form'].errors))
        self.assertEquals(1, len(response.context['form'].errors['__all__']))
        self.assertEquals('Minimum channels must be less than or equal to maximum channels.', response.context['form'].errors['__all__'][0])

    def test_only_integers_accepted_for_size_and_channels(self):
        # Act
        response = self.client.get(f'{reverse("advanced_search")}?query=visions&minChannels=abc&maxChannels=2.1&minSize=twerm&maxSize=0.00001&type=title')
    
        # Assert
        self.assertEquals(4, len(response.context['form'].errors))
        self.assertEquals('Enter a whole number.', response.context['form'].errors['maxChannels'][0])
        self.assertEquals('Enter a whole number.', response.context['form'].errors['minChannels'][0])
        self.assertEquals('Enter a whole number.', response.context['form'].errors['maxSize'][0])
        self.assertEquals('Enter a whole number.', response.context['form'].errors['minSize'][0])

    def test_searches_by_filename(self):
        # Act
        response = self.client.get(f'{reverse("advanced_search")}?query=blerp&type=filename')

        # Assert
        self.assertEquals(2, len(response.context['search_results']))
        self.assertEquals(self.song_visions_s3m, response.context['search_results'][0])
        self.assertEquals(self.song_visions_mod, response.context['search_results'][1])

    def test_searches_by_comment_text(self):
        # Act
        response = self.client.get(f'{reverse("advanced_search")}?query=flerp&type=comment-text')

        # Assert
        self.assertEquals(2, len(response.context['search_results']))
        self.assertEquals(self.song_visions_it, response.context['search_results'][0])
        self.assertEquals(self.song_visions_it2, response.context['search_results'][1])

    def test_searches_by_instrument_text(self):
        # Act
        response = self.client.get(f'{reverse("advanced_search")}?query=flerp&type=instrument-text')

        # Assert
        self.assertEquals(2, len(response.context['search_results']))
        self.assertEquals(self.song_visions_it2, response.context['search_results'][0])
        self.assertEquals(self.song_visions_xm, response.context['search_results'][1])

    def test_searches_by_combined_comment_and_instrument_text(self):
        # Act
        response = self.client.get(f'{reverse("advanced_search")}?query=flerp&type=instrument-text&type=comment-text')

        # Assert
        self.assertEquals(3, len(response.context['search_results']))
        self.assertEquals(self.song_visions_it, response.context['search_results'][0])
        self.assertEquals(self.song_visions_it2, response.context['search_results'][1])
        self.assertEquals(self.song_visions_xm, response.context['search_results'][2])

    def test_searches_by_combined_title_and_comment_text(self):
        # Act
        response = self.client.get(f'{reverse("advanced_search")}?query=flerp&type=title&type=comment-text')

        # Assert
        self.assertEquals(3, len(response.context['search_results']))
        self.assertEquals(self.song_flerp, response.context['search_results'][0])
        self.assertEquals(self.song_visions_it, response.context['search_results'][1])
        self.assertEquals(self.song_visions_it2, response.context['search_results'][2])
    
    def test_searches_by_combined_title_and_filename(self):
        # Act
        response = self.client.get(f'{reverse("advanced_search")}?query=flerp&type=title&type=filename')

        # Assert
        self.assertEquals(2, len(response.context['search_results']))
        self.assertEquals(self.song_flerp, response.context['search_results'][0])
        self.assertEquals(self.song_flerp_filename, response.context['search_results'][1])

    def test_searches_are_divided_by_page(self):
        # Arrange
        formats = [Song.Formats.MOD, Song.Formats.S3M, Song.Formats.IT, Song.Formats.XM]

        for i in range(30):
            title = f"Space {random.choice(['Jam', 'Funk', 'Rock', 'Pop', 'Boogie', 'Symphony'])}"
            format = random.choice(formats)
            filename_ext = format.name.lower()
            filename = f"{title.lower().replace(' ', '_')}.{filename_ext}"
            song = song_factories.SongFactory(title=title, format=format, filename=filename)

        # Page 1
        response = self.client.get(f'{reverse("advanced_search")}?query=space&type=title')
        self.assertEquals(25, len(response.context['search_results']))

        # Page 2
        response = self.client.get(f'{reverse("advanced_search")}?query=space&type=title&page=2')
        self.assertEquals(5, len(response.context['search_results']))