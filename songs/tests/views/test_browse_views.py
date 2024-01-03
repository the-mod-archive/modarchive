from django.test import TestCase
from django.urls import reverse

from songs import factories as song_factories
from songs.models import Song

BROWSE_SONGS_TEMPLATE = 'browse_songs.html'
PAGE_1 = "?page=1"
PAGE_2 = "?page=2"

class BrowseSongsByFilenameViewTests(TestCase):
    def setUp(self):
        self.songs = [
            song_factories.SongFactory(filename="Fading-Memories.mod", title="Fading Memories"),
            song_factories.SongFactory(filename="FutureVisions.s3m", title="Future Visions"),
            song_factories.SongFactory(filename="FantasyLand.it", title="Fantasy Land"),
            song_factories.SongFactory(filename="FireAndIce.xm", title="Fire and Ice"),
            song_factories.SongFactory(filename="Falling-Star.mod", title="Falling Star"),
            song_factories.SongFactory(filename="FreeSpirit.s3m", title="Free Spirit"),
            song_factories.SongFactory(filename="ForgottenDreams.it", title="Forgotten Dreams"),
            song_factories.SongFactory(filename="FierceBattle.xm", title="Fierce Battle"),
            song_factories.SongFactory(filename="FadingEchoes.mod", title="Fading Echoes"),
            song_factories.SongFactory(filename="FutureHorizon.s3m", title="Future Horizon"),
            song_factories.SongFactory(filename="GloriousDay.mod", title="Glorious Day"),
            song_factories.SongFactory(filename="GoldenEchoes.s3m", title="Golden Echoes"),
            song_factories.SongFactory(filename="GreenFields.it", title="Green Fields"),
            song_factories.SongFactory(filename="GentleRain.xm", title="Gentle Rain"),
            song_factories.SongFactory(filename="GalacticJourney.mod", title="Galactic Journey")    
        ]

    def test_browse_by_filename_view_uses_correct_template(self):
        response = self.client.get(reverse('browse_by_filename', kwargs={'query': 'f'}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, BROWSE_SONGS_TEMPLATE)

    def test_browse_by_filename_view_lists_correct_songs(self):
        response = self.client.get(reverse('browse_by_filename', kwargs={'query': 'f'}))
        self.assertEqual(response.status_code, 200)
        filtered_songs = list(filter(lambda song:song.filename[0]=="F", self.songs))
        self.assertCountEqual(list(response.context_data['songs']), filtered_songs)

    def test_browse_by_filename_view_lists_correct_songs_in_order(self):
        response = self.client.get(reverse('browse_by_filename', kwargs={'query': 'f'}))
        self.assertEqual(response.status_code, 200)
        filtered_songs = Song.objects.filter(filename__istartswith='F').order_by('filename')
        self.assertEqual(list(response.context_data['songs']), list(filtered_songs))

    def test_browse_by_filename_view_accepts_valid_input(self):
        for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_":
            response = self.client.get(reverse('browse_by_filename', kwargs={'query': c}))
            self.assertEqual(response.status_code, 200)

    def test_browse_by_filename_view_redirects_to_home_for_invalid_input(self):
        response = self.client.get(reverse('browse_by_filename', kwargs={'query': '&'}))
        self.assertRedirects(response, reverse('home'))

class BrowseSongsByLicenseViewTests(TestCase):
    def test_browse_by_license_view_uses_correct_template(self):
        response = self.client.get(reverse('browse_by_license', kwargs={'query': 'by'}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, BROWSE_SONGS_TEMPLATE)

    def test_browse_by_license_view_lists_correct_songs(self):
        songs = [
            song_factories.SongFactory(license=Song.Licenses.ATTRIBUTION),
            song_factories.SongFactory(license=Song.Licenses.ATTRIBUTION),
            song_factories.SongFactory(license=Song.Licenses.ATTRIBUTION),
            song_factories.SongFactory(license=Song.Licenses.ATTRIBUTION),
            song_factories.SongFactory(license=Song.Licenses.ATTRIBUTION),
            song_factories.SongFactory(license=Song.Licenses.ATTRIBUTION),
            song_factories.SongFactory(license=Song.Licenses.PUBLIC_DOMAIN),
            song_factories.SongFactory(license=Song.Licenses.PUBLIC_DOMAIN),
            song_factories.SongFactory(license=Song.Licenses.PUBLIC_DOMAIN)
        ]
        
        # Pass 1: attribution
        response = self.client.get(reverse('browse_by_license', kwargs={'query': Song.Licenses.ATTRIBUTION}))
        self.assertEqual(response.status_code, 200)
        filtered_songs = list(filter(lambda song:song.license==Song.Licenses.ATTRIBUTION, songs))
        self.assertCountEqual(list(response.context_data['songs']), filtered_songs)

        # Pass 2: public domain
        response = self.client.get(reverse('browse_by_license', kwargs={'query': Song.Licenses.PUBLIC_DOMAIN}))
        self.assertEqual(response.status_code, 200)
        filtered_songs = list(filter(lambda song:song.license==Song.Licenses.PUBLIC_DOMAIN, songs))
        self.assertCountEqual(list(response.context_data['songs']), filtered_songs)

    def test_browse_by_license_view_paginates_correctly(self):
        for _ in range(50):
            song_factories.SongFactory(license=Song.Licenses.SHARE_ALIKE)

        # Page 1
        response = self.client.get(reverse('browse_by_license', kwargs={'query': Song.Licenses.SHARE_ALIKE}) + PAGE_1)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(40, len(response.context_data['songs']))

        # Page 2
        response = self.client.get(reverse('browse_by_license', kwargs={'query': Song.Licenses.SHARE_ALIKE}) + PAGE_2)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(10, len(response.context_data['songs']))

    def test_browse_by_license_view_accepts_valid_query_params(self):
        for l in Song.Licenses:
            response = self.client.get(reverse('browse_by_license', kwargs={'query': l}))
            self.assertEqual(response.status_code, 200)

    def test_browse_by_license_view_rejects_invalid_query_params(self):
        response = self.client.get(reverse('browse_by_license', kwargs={'query': 'blarg'}))
        self.assertRedirects(response, reverse('home'))

class BrowseSongsByGenreViewTests(TestCase):
    def test_browse_by_genre_view_uses_correct_template(self):
        response = self.client.get(reverse('browse_by_genre', kwargs={'query': Song.Genres.DEMO_STYLE}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, BROWSE_SONGS_TEMPLATE)

    def test_browse_by_genre_view_lists_correct_songs(self):
        songs = [
            song_factories.SongFactory(genre=Song.Genres.DEMO_STYLE),
            song_factories.SongFactory(genre=Song.Genres.DEMO_STYLE),
            song_factories.SongFactory(genre=Song.Genres.DEMO_STYLE),
            song_factories.SongFactory(genre=Song.Genres.DEMO_STYLE),
            song_factories.SongFactory(genre=Song.Genres.DEMO_STYLE),
            song_factories.SongFactory(genre=Song.Genres.ELECTRONIC_TECHNO),
            song_factories.SongFactory(genre=Song.Genres.ELECTRONIC_TECHNO),
            song_factories.SongFactory(genre=Song.Genres.ELECTRONIC_TECHNO),
            song_factories.SongFactory(genre=Song.Genres.ELECTRONIC_TECHNO),
        ]

        # Pass 1: demostyle
        response = self.client.get(reverse('browse_by_genre', kwargs={'query': Song.Genres.DEMO_STYLE}))
        self.assertEqual(response.status_code, 200)
        filtered_songs = list(filter(lambda song:song.genre==Song.Genres.DEMO_STYLE, songs))
        self.assertCountEqual(list(response.context_data['songs']), filtered_songs)

        # Pass 2: techno
        response = self.client.get(reverse('browse_by_genre', kwargs={'query': Song.Genres.ELECTRONIC_TECHNO}))
        self.assertEqual(response.status_code, 200)
        filtered_songs = list(filter(lambda song:song.genre==Song.Genres.ELECTRONIC_TECHNO, songs))
        self.assertCountEqual(list(response.context_data['songs']), filtered_songs)

    def test_browse_by_genre_view_paginates_correctly(self):
        for _ in range(50):
            song_factories.SongFactory(genre=Song.Genres.ALTERNATIVE_METAL)

        # Page 1
        response = self.client.get(reverse('browse_by_genre', kwargs={'query': Song.Genres.ALTERNATIVE_METAL}) + PAGE_1)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(40, len(response.context_data['songs']))

        # Page 2
        response = self.client.get(reverse('browse_by_genre', kwargs={'query': Song.Genres.ALTERNATIVE_METAL}) + PAGE_2)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(10, len(response.context_data['songs']))

    def test_browse_by_genre_view_accepts_valid_query_params(self):
        for g in Song.Genres:
            response = self.client.get(reverse('browse_by_genre', kwargs={'query': g}))
            self.assertEqual(response.status_code, 200)

    def test_browse_by_genre_view_rejects_invalid_query_params(self):
        response = self.client.get(reverse('browse_by_genre', kwargs={'query': 'blarg'}))
        self.assertRedirects(response, reverse('home'))

class BrowseSongsByRatingTest(TestCase):
    def test_browse_by_rating_view_uses_correct_template(self):
        response = self.client.get(reverse('browse_by_rating', kwargs={'query': 9}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, BROWSE_SONGS_TEMPLATE)

    def test_browse_by_rating_view_includes_correct_songs(self):
        temp_songs = [
            song_factories.SongFactory(title="1"),
            song_factories.SongFactory(title="2"),
            song_factories.SongFactory(title="3"),
            song_factories.SongFactory(title="4"),
            song_factories.SongFactory(title="5"),
            song_factories.SongFactory(title="6"),
            song_factories.SongFactory(title="7"),
            song_factories.SongFactory(title="8")
        ]

        song_factories.SongStatsFactory(song=temp_songs[0], average_comment_score=9.0)
        song_factories.SongStatsFactory(song=temp_songs[1], average_comment_score=9.1)
        song_factories.SongStatsFactory(song=temp_songs[2], average_comment_score=9.2)
        song_factories.SongStatsFactory(song=temp_songs[3], average_comment_score=9.3)
        song_factories.SongStatsFactory(song=temp_songs[4], average_comment_score=10.0)
        song_factories.SongStatsFactory(song=temp_songs[5], average_comment_score=8.0)
        song_factories.SongStatsFactory(song=temp_songs[6], average_comment_score=8.0)
        song_factories.SongStatsFactory(song=temp_songs[7], average_comment_score=8.1)

        # Search for 9+
        response = self.client.get(reverse('browse_by_rating', kwargs={'query': 9}))
        self.assertEqual(response.status_code, 200)
        filtered_songs = list(filter(lambda song:song.songstats.average_comment_score >= 9.0, temp_songs))
        self.assertCountEqual(list(response.context_data['songs']), filtered_songs)

        # Search for 8's
        response = self.client.get(reverse('browse_by_rating', kwargs={'query': 8}))
        filtered_songs = list(filter(lambda song:song.songstats.average_comment_score < 9.0, temp_songs))
        self.assertCountEqual(list(response.context_data['songs']), filtered_songs)

    def test_browse_by_rating_view_paginates_correctly(self):
        for _ in range(50):
            song = song_factories.SongFactory()
            song_factories.SongStatsFactory(average_comment_score=10.0, song=song)

        # Page 1
        response = self.client.get(reverse('browse_by_rating', kwargs={'query': 9}) + PAGE_1)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(40, len(response.context_data['songs']))

        # Page 2
        response = self.client.get(reverse('browse_by_rating', kwargs={'query': 9}) + PAGE_2)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(10, len(response.context_data['songs']))

    def test_browse_by_rating_view_accepts_valid_query_params(self):
        for r in [9, 8, 7, 6, 5, 4, 3, 2, 1]:
            response = self.client.get(reverse('browse_by_rating', kwargs={'query': r}))
            self.assertEqual(response.status_code, 200)

    def test_browse_by_genre_view_rejects_invalid_query_params(self):
        response = self.client.get(reverse('browse_by_rating', kwargs={'query': 11}))
        self.assertRedirects(response, reverse('home'))
