from django.test import TestCase
from django.urls import reverse

from artists.tests import factories as artist_factories
from homepage.tests import factories
from songs.factories import SongFactory
from songs.models import Song
from interactions.factories import ArtistCommentFactory
from interactions.models import ArtistComment

class SongDetailsTests(TestCase):
    OLD_TITLE = "Old title"
    NEW_TITLE = "New title"
    OLD_TEXT = "Old text"
    NEW_TEXT = "New text"

    def test_requires_authentication(self):
        # Arrange
        user = factories.UserFactory()
        song = SongFactory()
        artist_factories.ArtistFactory(user=user, profile=user.profile, songs=(song,))

        update_song_details_url = reverse('song_details', kwargs={'pk': song.id})
        login_url = reverse('login')

        # GET test
        response=self.client.get(update_song_details_url)
        self.assertRedirects(response, f"{login_url}?next={update_song_details_url}")

        # POST test
        response=self.client.post(update_song_details_url, {'genre': Song.Genres.ELECTRONIC_GENERAL})
        self.assertRedirects(response, f"{login_url}?next={update_song_details_url}")

    def test_cannot_update_details_of_somebody_elses_song(self):
        # Arrange
        user = factories.UserFactory()
        user_2 = factories.UserFactory()
        song = SongFactory(clean_title=self.OLD_TITLE)
        artist_factories.ArtistFactory(user=user, profile=user.profile)
        artist_factories.ArtistFactory(user=user_2, profile=user_2.profile, songs=(song,))
        self.client.force_login(user)

        # GET test
        response=self.client.get(reverse('song_details', kwargs={'pk': song.id}))
        self.assertRedirects(response, reverse('view_song', kwargs = {'pk': song.id}))

        # POST test
        response=self.client.post(reverse('song_details', kwargs={'pk': song.id}), {'genre': Song.Genres.ELECTRONIC_GENERAL, 'clean_title': self.NEW_TITLE})
        self.assertRedirects(response, reverse('view_song', kwargs = {'pk': song.id}))
        song.refresh_from_db()
        self.assertEqual(None, song.genre)
        self.assertEqual(self.OLD_TITLE, song.clean_title)

    def test_happy_path_updates_all_fields(self):
        # Arrange
        user = factories.UserFactory()
        song = SongFactory(clean_title=self.OLD_TITLE, genre=Song.Genres.ALTERNATIVE)
        artist_factories.ArtistFactory(user=user, profile=user.profile, songs=(song,))
        comment = ArtistCommentFactory(profile=user.profile, song=song, text=self.OLD_TEXT)
        self.client.force_login(user)

        # GET test
        response=self.client.get(reverse('song_details', kwargs={'pk': song.id}))
        self.assertTemplateUsed(response, 'update_song_details.html')
        self.assertEqual(song, response.context['object'])

        # POST test
        response=self.client.post(reverse('song_details', kwargs={'pk': song.id}), {'genre': Song.Genres.ELECTRONIC_GENERAL, 'clean_title': self.NEW_TITLE, 'text': self.NEW_TEXT})
        self.assertRedirects(response, reverse('view_song', kwargs = {'pk': song.id}))
        song.refresh_from_db()
        self.assertEqual(self.NEW_TITLE, song.clean_title)
        self.assertEqual(Song.Genres.ELECTRONIC_GENERAL, song.genre)
        comment.refresh_from_db()
        self.assertEqual(self.NEW_TEXT, comment.text)

    def test_adding_text_creates_new_artist_comment(self):
        # Arrange
        user = factories.UserFactory()
        song = SongFactory(clean_title=self.OLD_TITLE)
        artist_factories.ArtistFactory(user=user, profile=user.profile, songs=(song,))
        self.client.force_login(user)

        # Act
        response=self.client.post(reverse('song_details', kwargs={'pk': song.id}), {'genre': Song.Genres.ELECTRONIC_GENERAL, 'text': self.NEW_TEXT})

        # Assert
        self.assertRedirects(response, reverse('view_song', kwargs = {'pk': song.id}))
        song.refresh_from_db()
        self.assertEqual(Song.Genres.ELECTRONIC_GENERAL, song.genre)
        self.assertIsNone(song.clean_title)
        comment = ArtistComment.objects.get(song=song, profile=user.profile)
        self.assertEqual(self.NEW_TEXT, comment.text)

    def test_removing_text_deletes_artist_comment(self):
        # Arrange
        user = factories.UserFactory()
        song = SongFactory(clean_title=self.OLD_TITLE)
        artist_factories.ArtistFactory(user=user, profile=user.profile, songs=(song,))
        ArtistCommentFactory(profile=user.profile, song=song, text=self.OLD_TEXT)
        self.client.force_login(user)

        # Act
        response=self.client.post(reverse('song_details', kwargs={'pk': song.id}), {'text': ''})

        # Assert
        self.assertRedirects(response, reverse('view_song', kwargs = {'pk': song.id}))
        query_set = ArtistComment.objects.filter(song=song, profile=user.profile)
        self.assertEqual(0, len(query_set))

    def test_leaving_text_blank_does_not_create_new_artist_comment(self):
        # Arrange
        user = factories.UserFactory()
        song = SongFactory(clean_title=self.OLD_TITLE)
        artist_factories.ArtistFactory(user=user, profile=user.profile, songs=(song,))
        self.client.force_login(user)

        # Act
        response=self.client.post(reverse('song_details', kwargs={'pk': song.id}), {'text': ''})

        # Assert
        self.assertRedirects(response, reverse('view_song', kwargs = {'pk': song.id}))
        query_set = ArtistComment.objects.filter(song=song, profile=user.profile)
        self.assertEqual(0, len(query_set))

    def test_artist_only_creates_their_own_comment_to_song(self):
        # Arrange
        user = factories.UserFactory()
        user_2 = factories.UserFactory()
        song = SongFactory(clean_title=self.OLD_TITLE)
        artist_factories.ArtistFactory(user=user, profile=user.profile, songs=(song,))
        artist_factories.ArtistFactory(user=user_2, profile=user_2.profile, songs=(song,))
        self.client.force_login(user)

        # Act
        response=self.client.post(reverse('song_details', kwargs={'pk': song.id}), {'text': self.NEW_TEXT})

        # Assert
        self.assertRedirects(response, reverse('view_song', kwargs = {'pk': song.id}))
        self.assertEqual(1, len(ArtistComment.objects.filter(song=song, profile=user.profile)))
        self.assertEqual(0, len(ArtistComment.objects.filter(song=song, profile=user_2.profile)))

    def test_artist_only_modifies_their_own_comment_to_song(self):
        # Arrange
        user = factories.UserFactory()
        user_2 = factories.UserFactory()
        song = SongFactory(clean_title=self.OLD_TITLE)
        artist_factories.ArtistFactory(user=user, profile=user.profile, songs=(song,))
        artist_factories.ArtistFactory(user=user_2, profile=user_2.profile, songs=(song,))
        ArtistCommentFactory(profile=user.profile, song=song, text=self.OLD_TEXT)
        ArtistCommentFactory(profile=user_2.profile, song=song, text=self.OLD_TEXT)
        self.client.force_login(user)

        # Act
        response=self.client.post(reverse('song_details', kwargs={'pk': song.id}), {'text': self.NEW_TEXT})

        # Assert
        self.assertRedirects(response, reverse('view_song', kwargs = {'pk': song.id}))
        query_set_1 = ArtistComment.objects.filter(song=song, profile=user.profile)
        query_set_2 = ArtistComment.objects.filter(song=song, profile=user_2.profile)
        self.assertEqual(1, len(query_set_1))
        self.assertEqual(1, len(query_set_2))
        self.assertEqual(self.NEW_TEXT, query_set_1[0].text)
        self.assertEqual(self.OLD_TEXT, query_set_2[0].text)

    def test_artist_only_deletes_their_own_comment_to_song(self):
        # Arrange
        user = factories.UserFactory()
        user_2 = factories.UserFactory()
        song = SongFactory(clean_title=self.OLD_TITLE)
        artist_factories.ArtistFactory(user=user, profile=user.profile, songs=(song,))
        artist_factories.ArtistFactory(user=user_2, profile=user_2.profile, songs=(song,))
        ArtistCommentFactory(profile=user.profile, song=song, text=self.OLD_TEXT)
        ArtistCommentFactory(profile=user_2.profile, song=song, text=self.OLD_TEXT)
        self.client.force_login(user)

        # Act
        response=self.client.post(reverse('song_details', kwargs={'pk': song.id}), {'text': ''})

        # Assert
        self.assertRedirects(response, reverse('view_song', kwargs = {'pk': song.id}))
        query_set_1 = ArtistComment.objects.filter(song=song, profile=user.profile)
        query_set_2 = ArtistComment.objects.filter(song=song, profile=user_2.profile)
        self.assertEqual(0, len(query_set_1))
        self.assertEqual(1, len(query_set_2))
