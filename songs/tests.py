import os
import tempfile
import zipfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls.base import reverse
from unittest.mock import patch

from artists import factories as artist_factories
from homepage.tests import factories
from songs.models import ArtistComment, Favorite, Song, NewSong
from songs.templatetags import filters
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
        artist_factories.ArtistFactory(songs=(song,song_2), user=user, profile=user.profile)
        song_factories.ArtistCommentFactory(song=song, profile=user.profile, text="hi")

        self.assertTrue(song.has_artist_commented(user.profile.id))
        self.assertFalse(song_2.has_artist_commented(user.profile.id))
        self.assertFalse(song_3.has_artist_commented(user.profile.id))

    def test_display_file_size(self):
        song = song_factories.SongFactory(file_size = 5000)
        song_2 = song_factories.SongFactory(file_size = 259871)
        song_3 = song_factories.SongFactory(file_size = 2716816)
        self.assertEquals("5000 bytes", song.display_file_size())
        self.assertEquals("259.87 KB", song_2.display_file_size())
        self.assertEquals("2.72 MB", song_3.display_file_size())

    def test_retrieves_stats_correctly(self):
        # Arrange
        song = song_factories.SongFactory()
        song_factories.SongStatsFactory(song = song, downloads=123, total_comments=5, average_comment_score=8.0)

        # Act
        stats = song.get_stats()

        # Assert
        self.assertEquals(123, stats.downloads)
        self.assertEquals(5, stats.total_comments)
        self.assertEquals(8.0, stats.average_comment_score)

    def test_creates_stats_if_not_already_existing(self):
        # Arrange
        song = song_factories.SongFactory()

        # Act
        stats = song.get_stats()

        # Assert
        self.assertEquals(0, stats.downloads)
        self.assertEquals(0, stats.total_comments)
        self.assertEquals(0.0, stats.average_comment_score)

class CommentModelTests(TestCase):
    def test_song_stats_updated_correctly_after_removing_comment(self):
        song = song_factories.SongFactory()
        song_factories.SongStatsFactory(song=song)
        comment_1 = song_factories.CommentFactory(song=song, rating=10)
        comment_2 = song_factories.CommentFactory(song=song, rating=5)

        self.assertEquals(2, song.songstats.total_comments)
        self.assertEquals(7.5, song.songstats.average_comment_score)

        comment_1.delete()
        
        self.assertEquals(1, song.songstats.total_comments)
        self.assertEquals(5.0, song.songstats.average_comment_score)

    def test_song_stats_updated_correctly_after_removing_final_comment(self):
        song = song_factories.SongFactory()
        song_factories.SongStatsFactory(song=song)
        comment_1 = song_factories.CommentFactory(song=song, rating=10)

        comment_1.delete()

        self.assertEquals(0, song.songstats.total_comments)
        self.assertEquals(0.0, song.songstats.average_comment_score)

class SongListTests(TestCase):
    def test_song_list_view_contains_all_songs(self):
        # Arrange
        expected_length = 10
        for n in range(expected_length):
            song_factories.SongFactory()
        
        # Act
        response = self.client.get(reverse('songs'))
        
        # Assert
        actual_length = len(response.context['object_list'])
        
        self.assertTemplateUsed(response, 'song_list.html')
        self.assertTrue('object_list' in response.context)
        self.assertEqual(expected_length, actual_length, f"Expected {expected_length} objects in songs list but got {actual_length}")

class ViewSongTests(TestCase):
    def test_context_contains_song_and_comments(self):
        song = song_factories.SongFactory(filename="file2.s3m", title="File 2")
        song_factories.SongStatsFactory(song=song)
        response = self.client.get(reverse('view_song', kwargs = {'pk': song.id}))
        song_factories.CommentFactory(song=song, rating=10, text="This was definitely a song!")
        song_factories.CommentFactory(song=song, rating=5, text="I disagree, this was not a song.")

        self.assertTrue('song' in response.context)
        song = response.context['song']
        self.assertEquals("file2.s3m", song.filename)
        self.assertEquals("File 2", song.get_title())
        self.assertEquals(2, len(song.comment_set.all()))
        self.assertEquals("This was definitely a song!", song.comment_set.all()[0].text)
        self.assertEquals("I disagree, this was not a song.", song.comment_set.all()[1].text)
        self.assertEquals(10, song.comment_set.all()[0].rating)
        self.assertEquals(5, song.comment_set.all()[1].rating)

    def test_unauthenticated_user_cannot_comment(self):
        # Arrange
        song = song_factories.SongFactory(filename="file2.s3m", title="File 2", songstats=song_factories.SongStatsFactory())
        
        # Act
        response = self.client.get(reverse('view_song', kwargs = {'pk': song.id}))

        # Assert
        self.assertFalse('can_comment' in response.context)

    def test_user_can_comment_if_has_not_commented(self):
        # Arrange
        user = factories.UserFactory()
        song = song_factories.SongFactory()
        self.client.force_login(user)
        
        # Act
        response = self.client.get(reverse('view_song', kwargs = {'pk': song.id}))

        # Assert
        self.assertTrue(response.context['can_comment'])

    def test_user_cannot_comment_if_has_already_commented(self):
        # Arrange
        user = factories.UserFactory()
        song = song_factories.SongFactory()
        song_factories.CommentFactory(song=song, profile=user.profile, rating=10, text="This was definitely a song!")
        self.client.force_login(user)

        # Act
        response = self.client.get(reverse('view_song', kwargs = {'pk': song.id}))

        # Assert
        self.assertFalse(response.context['can_comment'])
        

    def test_user_can_comment_when_not_the_song_composer(self):
        # Arrange
        user = factories.UserFactory()
        song = song_factories.SongFactory()
        artist_factories.ArtistFactory(songs=(song,))
        self.client.force_login(user)

        # Act
        response = self.client.get(reverse('view_song', kwargs = {'pk': song.id}))

        # Assert
        self.assertTrue(response.context['can_comment'])

    def test_user_cannot_comment_if_is_song_composer(self):
        # Arrange
        user = factories.UserFactory()
        song = song_factories.SongFactory()
        artist_factories.ArtistFactory(songs=(song,), profile=user.profile)
        self.client.force_login(user)

        # Act
        response = self.client.get(reverse('view_song', kwargs = {'pk': song.id}))

        # Assert
        self.assertFalse(response.context['can_comment'])

    def test_is_favorite_is_not_present_when_not_authenticated(self):
        # Arrange
        song = song_factories.SongFactory()

        # Act
        response = self.client.get(reverse('view_song', kwargs = {'pk': song.id}))

        # Assert
        self.assertFalse(hasattr(response.context, 'is_favorite'))

    def test_is_favorite_is_false_when_not_favorited(self):
        # Arrange
        song = song_factories.SongFactory()
        user = factories.UserFactory()
        self.client.force_login(user)

        # Act
        response = self.client.get(reverse('view_song', kwargs = {'pk': song.id}))

        # Assert
        self.assertFalse(response.context['is_favorite'])

    def test_is_favorite_is_true_when_favorited(self):
        # Arrange
        song = song_factories.SongFactory()
        user = factories.UserFactory()
        self.client.force_login(user)
        song_factories.FavoriteFactory(profile=user.profile, song=song)

        # Act
        response = self.client.get(reverse('view_song', kwargs = {'pk': song.id}))

        # Assert
        self.assertTrue(response.context['is_favorite'])

    def test_artist_can_comment_is_false_when_own_song_and_has_commented(self):
        # Arrange
        user = factories.UserFactory()
        song = song_factories.SongFactory()
        artist_factories.ArtistFactory(songs=[song], user=user, profile=user.profile)
        song_factories.ArtistCommentFactory(song=song, profile=user.profile, text="hi")
        self.client.force_login(user)
        
        # Act
        response = self.client.get(reverse('view_song', kwargs = {'pk': song.id}))

        # Assert
        self.assertFalse(response.context['artist_can_comment'])

    def test_artist_can_comment_is_true_when_own_song_and_has_not_commented(self):
        # Arrange
        user = factories.UserFactory()
        song = song_factories.SongFactory()
        artist_factories.ArtistFactory(songs=[song], user=user, profile=user.profile)
        self.client.force_login(user)

        # Act
        response = self.client.get(reverse('view_song', kwargs = {'pk': song.id}))

        # Assert
        self.assertTrue(response.context['artist_can_comment'])

    def test_artist_can_comment_is_false_when_not_own_song(self):
        # Arrange
        user = factories.UserFactory()
        song = song_factories.SongFactory()
        artist_factories.ArtistFactory(songs=[], user=user, profile=user.profile)
        self.client.force_login(user)

        # Act
        response = self.client.get(reverse('view_song', kwargs = {'pk': song.id}))

        # Assert
        self.assertFalse(response.context['artist_can_comment'])

    def test_artist_can_comment_is_not_present_when_not_authenticated(self):
        # Arrange
        song = song_factories.SongFactory()

        # Act
        response = self.client.get(reverse('view_song', kwargs = {'pk': song.id}))

        # Assert
        self.assertFalse(hasattr(response.context, 'artist_can_comment'))

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
        self.assertEquals(stats.downloads + 1, song.songstats.downloads)

    def test_returns_404_if_song_id_is_missing(self):
        # Act
        response = self.client.get("/songs/1000/download")
        
        # Assert
        self.assertEqual(response.status_code, 404)

class AddCommentTests(TestCase):
    def test_get_add_comment_page_happy_path(self):
        # Arrange
        user = factories.UserFactory()
        song = song_factories.SongFactory()
        self.client.force_login(user)

        # Act
        response = self.client.get(reverse('add_comment', kwargs={'pk': song.id}))

        # Assert
        self.assertEquals(200, response.status_code)
        self.assertTemplateUsed(response, "add_comment.html")
        self.assertEquals(song.id, response.context['song'].id)
        self.assertEquals(song.title, response.context['song'].get_title())

    def test_post_add_comment_happy_path(self):
        # Arrange
        user = factories.UserFactory()
        song = song_factories.SongFactory()
        self.client.force_login(user)

        # Act
        response = self.client.post(reverse('add_comment', kwargs={'pk': song.id}), {'rating': 10, 'text': "This is my review"})

        # Assert
        self.assertRedirects(response, reverse('view_song', kwargs = {'pk': song.id}))
        self.assertEquals(1, len(song.comment_set.all()))

    def test_post_add_comment_calculates_stats_correctly(self):
        # Arrange
        user = factories.UserFactory()
        song = song_factories.SongFactory()
        song_factories.SongStatsFactory(song=song)
        self.client.force_login(user)
        
        # Act
        self.client.post(reverse('add_comment', kwargs={'pk': song.id}), {'rating': 10, 'text': "This is my review"})

        # Assert
        song.refresh_from_db()
        self.assertEquals(1, len(song.comment_set.all()))
        self.assertEquals(1, song.songstats.total_comments)
        self.assertEquals(10.0, song.songstats.average_comment_score)

    def test_post_add_comment_calculates_stats_correctly_with_existing_comments(self):
        # Arrange
        user = factories.UserFactory()
        song = song_factories.SongFactory()
        song_factories.SongStatsFactory(song=song)
        song_factories.CommentFactory(song=song, rating=5, text='some review')
        self.client.force_login(user)

        # Act
        self.client.post(reverse('add_comment', kwargs={'pk': song.id}), {'rating': 10, 'text': "This is my review"})

        # Assert
        song.refresh_from_db()
        self.assertEquals(2, len(song.comment_set.all()))
        self.assertEquals(2, song.songstats.total_comments)
        self.assertEquals(7.5, song.songstats.average_comment_score)

    def test_post_add_comment_calculates_stats_correctly_when_stats_object_not_created_yet(self):
        # Arrange
        user = factories.UserFactory()
        song = song_factories.SongFactory()
        self.client.force_login(user)
        
        # Act
        self.client.post(reverse('add_comment', kwargs={'pk': song.id}), {'rating': 10, 'text': "This is my review"})

        # Assert
        song.refresh_from_db()
        self.assertEquals(1, len(song.comment_set.all()))
        self.assertEquals(1, song.songstats.total_comments)
        self.assertEquals(10.0, song.songstats.average_comment_score)

    def test_get_user_redirected_for_own_song(self):
        # Arrange
        user = factories.UserFactory()
        song = song_factories.SongFactory()
        artist_factories.ArtistFactory(user=user, profile=user.profile, songs=(song,))
        self.client.force_login(user)

        # Act
        response = self.client.get(reverse('add_comment', kwargs={'pk': song.id}))

        # Assert
        self.assertRedirects(response, reverse('view_song', kwargs = {'pk': song.id}))

    def test_post_user_redirected_for_own_song(self):
        # Arrange
        user = factories.UserFactory()
        song = song_factories.SongFactory()
        artist_factories.ArtistFactory(user=user, profile=user.profile, songs=(song,))
        self.client.force_login(user)

        # Act
        response = self.client.post(reverse('add_comment', kwargs={'pk': song.id}), {'rating': 10, 'text': "This is my review"})

        # Assert
        self.assertRedirects(response, reverse('view_song', kwargs = {'pk': song.id}))
        self.assertEquals(0, Song.objects.get(id=song.id).comment_set.all().count())

    def test_get_user_redirected_when_already_commented(self):
        # Arrange
        user = factories.UserFactory()
        song = song_factories.SongFactory()
        song_factories.CommentFactory(profile=user.profile, song=song)
        self.client.force_login(user)

        # Act
        response = self.client.get(reverse('add_comment', kwargs={'pk': song.id}))

        # Assert
        self.assertRedirects(response, reverse('view_song', kwargs = {'pk': song.id}))

    def test_post_user_redirected_when_already_commented(self):
        # Arrange
        user = factories.UserFactory()
        song = song_factories.SongFactory()
        song_factories.CommentFactory(profile=user.profile, song=song)
        self.client.force_login(user)

        # Act
        response = self.client.post(reverse('add_comment', kwargs={'pk': song.id}), {'rating': 10, 'text': "This is my review"})

        # Assert
        self.assertRedirects(response, reverse('view_song', kwargs = {'pk': song.id}))
        self.assertEquals(1, Song.objects.get(id=song.id).comment_set.all().count())

    def test_get_redirect_unauthenticated_user(self):
        # Arrange
        add_comment_url = reverse('add_comment', kwargs={'pk': 2})
        login_url = reverse('login')

        # Act
        response = self.client.get(add_comment_url)

        # Assert
        self.assertRedirects(response, f"{login_url}?next={add_comment_url}")

    def test_post_redirect_unauthenticated_user(self):
        # Arrange
        add_comment_url = reverse('add_comment', kwargs={'pk': 2})
        login_url = reverse('login')

        # Act
        response = self.client.post(add_comment_url, {'rating': 10, 'text': "This is my review"})
        
        # Assert
        self.assertRedirects(response, f"{login_url}?next={add_comment_url}")

    def test_genre_form_available_when_song_has_no_genre(self):
        # Arrange
        user = factories.UserFactory()
        song = song_factories.SongFactory()
        self.client.force_login(user)

        # Act
        response = self.client.get(reverse('add_comment', kwargs={'pk': song.id}))

        # Assert
        self.assertTrue(response.context.get('song_form'))
        self.assertTrue(response.context['song_form'].fields.get('genre'))

    def test_genre_form_not_available_when_song_has_genre(self):
        # Arrange
        user = factories.UserFactory()
        song = song_factories.SongFactory(genre=Song.Genres.ELECTRONIC_GENERAL)
        self.client.force_login(user)

        # Act
        response = self.client.get(reverse('add_comment', kwargs={'pk': song.id}))

        # Assert
        self.assertFalse(response.context.get('song_form'))

    def test_post_genre_adds_genre_to_song_when_not_already_set(self):
        # Arrange
        user = factories.UserFactory()
        song = song_factories.SongFactory()
        self.client.force_login(user)

        # Act
        response = self.client.post(reverse('add_comment', kwargs={'pk': song.id}), {'rating': 10, 'text': "This is my review", 'genre': Song.Genres.ELECTRONIC_GENERAL})

        # Assert
        self.assertRedirects(response, reverse('view_song', kwargs = {'pk': song.id}))
        song.refresh_from_db()
        self.assertEquals(Song.Genres.ELECTRONIC_GENERAL, song.genre)

    def test_post_cannot_change_genre_if_already_set_in_song(self):
        # Arrange
        user = factories.UserFactory()
        song = song_factories.SongFactory(genre=Song.Genres.ELECTRONIC_GENERAL)
        self.client.force_login(user)

        # Act
        response = self.client.post(reverse('add_comment', kwargs={'pk': song.id}), {'rating': 10, 'text': "This is my review", 'genre': Song.Genres.ALTERNATIVE})

        # Assert
        self.assertRedirects(response, reverse('view_song', kwargs = {'pk': song.id}))
        song.refresh_from_db()
        self.assertEquals(Song.Genres.ELECTRONIC_GENERAL, song.genre)

    def test_post_leaving_genre_blank_does_not_set_genre_to_blank(self):
        # Arrange
        user = factories.UserFactory()
        song = song_factories.SongFactory(genre=Song.Genres.ELECTRONIC_GENERAL)
        self.client.force_login(user)

        # Act
        response = self.client.post(reverse('add_comment', kwargs={'pk': song.id}), {'rating': 10, 'text': "This is my review"})

        # Assert
        self.assertRedirects(response, reverse('view_song', kwargs = {'pk': song.id}))
        song.refresh_from_db()
        self.assertEquals(Song.Genres.ELECTRONIC_GENERAL, song.genre)

class FilterTests(TestCase):
    def test_email_address_filter_masks_single_email_address(self):
        comment = "You are listening to a mod by testguy@test.com which was written in 1996"
        filtered_comment = filters.hide_email_address(comment)
        self.assertEquals("You are listening to a mod by testguy_test.com which was written in 1996", filtered_comment)

    def test_email_address_filter_masks_multiple_email_addresses(self):
        comment = "You are listening to a mod by testguy@test.com and testguy2@test.com which was written in 1996"
        filtered_comment = filters.hide_email_address(comment)
        self.assertEquals("You are listening to a mod by testguy_test.com and testguy2_test.com which was written in 1996", filtered_comment)

    def test_email_address_filter_does_not_change_input_without_email_addresses(self):
        comment = "You are listening to a mod by testguy which was written in 1996"
        filtered_comment = filters.hide_email_address(comment)
        self.assertEquals(comment, filtered_comment)

class AddFavoriteTests(TestCase):
    def test_adds_favorite(self):
        song = song_factories.SongFactory()
        user = factories.UserFactory()
        self.client.force_login(user)
        
        # Act
        response = self.client.get(reverse('add_favorite', kwargs = {'pk': song.id}))

        # Assert
        self.assertRedirects(response, reverse('view_song', kwargs = {'pk': song.id}))
        self.assertEquals(1, Favorite.objects.filter(song_id=song.id, profile_id=user.profile.id).count())
        

    def test_does_not_add_favorite_when_already_favorited(self):
        # Arrange
        song = song_factories.SongFactory()
        user = factories.UserFactory()
        self.client.force_login(user)
        song_factories.FavoriteFactory(profile=user.profile, song=song)
        
        # Act
        response = self.client.get(reverse('add_favorite', kwargs = {'pk': song.id}))

        # Assert
        self.assertRedirects(response, reverse('view_song', kwargs = {'pk': song.id}))
        self.assertEquals(1, Favorite.objects.filter(song_id=song.id, profile_id=user.profile.id).count())

    def test_does_not_add_favorite_when_not_authenticated(self):
        # Arrange
        song = song_factories.SongFactory()
        login_url = reverse('login')
        add_favorite_url = reverse('add_favorite', kwargs = {'pk': song.id})

        # Act
        response = self.client.get(add_favorite_url)
        
        # Assert
        self.assertRedirects(response, f"{login_url}?next={add_favorite_url}")
        self.assertEquals(0, Favorite.objects.filter(song_id=song.id).count())

    def test_does_not_add_artists_own_song_as_favorite(self):
        # Arrange
        user = factories.UserFactory()
        song = song_factories.SongFactory()
        artist_factories.ArtistFactory(user=user, profile=user.profile, songs=(song,))
        self.client.force_login(user)

        # Act
        self.client.get(reverse('add_favorite', kwargs = {'pk': song.id}))

        # Assert
        self.assertEquals(0, Favorite.objects.filter(song_id=song.id).count())

class RemoveFavoriteTests(TestCase):
    def test_removes_favorite(self):
        # Arrange
        song = song_factories.SongFactory()
        user = factories.UserFactory()
        self.client.force_login(user)
        song_factories.FavoriteFactory(profile=user.profile, song=song)
        
        # Act
        response = self.client.get(reverse('remove_favorite', kwargs = {'pk': song.id}))

        # Assert
        self.assertRedirects(response, reverse('view_song', kwargs = {'pk': song.id}))
        self.assertEquals(0, Favorite.objects.filter(song_id=song.id, profile_id=user.profile.id).count())

    def test_does_not_remove_favorite_when_not_favorited(self):
        # Arrange
        song = song_factories.SongFactory()
        user = factories.UserFactory()
        self.client.force_login(user)
        
        # Act
        response = self.client.get(reverse('remove_favorite', kwargs = {'pk': song.id}))

        # Assert
        self.assertRedirects(response, reverse('view_song', kwargs = {'pk': song.id}))
        self.assertEquals(0, Favorite.objects.filter(song_id=song.id, profile_id=user.profile.id).count())

    def test_does_not_remove_favorite_when_not_authenticated(self):
        # Arrange
        song = song_factories.SongFactory()
        user = factories.UserFactory()
        login_url = reverse('login')
        remove_favorite_url = reverse('remove_favorite', kwargs = {'pk': song.id})
        song_factories.FavoriteFactory(profile=user.profile, song=song)

        # Act
        response = self.client.get(remove_favorite_url)
        
        # Assert
        self.assertRedirects(response, f"{login_url}?next={remove_favorite_url}")
        self.assertEquals(1, Favorite.objects.filter(song_id=song.id).count())

class RandomSongTests(TestCase):
    @patch('songs.views.choice')
    def test_redirects_to_random_song(self, mock_choice):
        # Arrange
        song1 = song_factories.SongFactory()
        song_factories.SongFactory()
        song_factories.SongFactory()
        song_factories.SongFactory()
        mock_choice.return_value = song1.id

        # Act
        response = self.client.get(reverse('random_song'))

        # Assert
        self.assertRedirects(response, reverse('view_song', kwargs = {'pk': song1.id}))

class SongDetailsTests(TestCase):
    old_title = "Old title"
    new_title = "New title"
    old_text = "Old text"
    new_text = "New text"

    def test_requires_authentication(self):
        # Arrange
        user = factories.UserFactory()
        song = song_factories.SongFactory()
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
        song = song_factories.SongFactory(clean_title=self.old_title)
        artist_factories.ArtistFactory(user=user, profile=user.profile)
        artist_factories.ArtistFactory(user=user_2, profile=user_2.profile, songs=(song,))
        self.client.force_login(user)

        # GET test
        response=self.client.get(reverse('song_details', kwargs={'pk': song.id}))
        self.assertRedirects(response, reverse('view_song', kwargs = {'pk': song.id}))

        # POST test
        response=self.client.post(reverse('song_details', kwargs={'pk': song.id}), {'genre': Song.Genres.ELECTRONIC_GENERAL, 'clean_title': self.new_title})
        self.assertRedirects(response, reverse('view_song', kwargs = {'pk': song.id}))
        song.refresh_from_db()
        self.assertEquals(None, song.genre)
        self.assertEquals(self.old_title, song.clean_title)

    def test_happy_path_updates_all_fields(self):
        # Arrange
        user = factories.UserFactory()
        song = song_factories.SongFactory(clean_title=self.old_title, genre=Song.Genres.ALTERNATIVE)
        artist_factories.ArtistFactory(user=user, profile=user.profile, songs=(song,))
        comment = song_factories.ArtistCommentFactory(profile=user.profile, song=song, text=self.old_text)
        self.client.force_login(user)

        # GET test
        response=self.client.get(reverse('song_details', kwargs={'pk': song.id}))
        self.assertTemplateUsed(response, 'update_song_details.html')
        self.assertEquals(song, response.context['object'])
        
        # POST test
        response=self.client.post(reverse('song_details', kwargs={'pk': song.id}), {'genre': Song.Genres.ELECTRONIC_GENERAL, 'clean_title': self.new_title, 'text': self.new_text})
        self.assertRedirects(response, reverse('view_song', kwargs = {'pk': song.id}))
        song.refresh_from_db()
        self.assertEquals(self.new_title, song.clean_title)
        self.assertEquals(Song.Genres.ELECTRONIC_GENERAL, song.genre)
        comment.refresh_from_db()
        self.assertEquals(self.new_text, comment.text)

    def test_adding_text_creates_new_artist_comment(self):
        # Arrange
        user = factories.UserFactory()
        song = song_factories.SongFactory(clean_title=self.old_title)
        artist_factories.ArtistFactory(user=user, profile=user.profile, songs=(song,))
        self.client.force_login(user)
        
        # Act
        response=self.client.post(reverse('song_details', kwargs={'pk': song.id}), {'genre': Song.Genres.ELECTRONIC_GENERAL, 'text': self.new_text})

        # Assert
        self.assertRedirects(response, reverse('view_song', kwargs = {'pk': song.id}))
        song.refresh_from_db()
        self.assertEquals(Song.Genres.ELECTRONIC_GENERAL, song.genre)
        self.assertIsNone(song.clean_title)
        comment = ArtistComment.objects.get(song=song, profile=user.profile)
        self.assertEquals(self.new_text, comment.text)

    def test_removing_text_deletes_artist_comment(self):
        # Arrange
        user = factories.UserFactory()
        song = song_factories.SongFactory(clean_title=self.old_title)
        artist_factories.ArtistFactory(user=user, profile=user.profile, songs=(song,))
        song_factories.ArtistCommentFactory(profile=user.profile, song=song, text=self.old_text)
        self.client.force_login(user)

        # Act
        response=self.client.post(reverse('song_details', kwargs={'pk': song.id}), {'text': ''})

        # Assert
        self.assertRedirects(response, reverse('view_song', kwargs = {'pk': song.id}))
        query_set = ArtistComment.objects.filter(song=song, profile=user.profile)
        self.assertEquals(0, len(query_set))

    def test_leaving_text_blank_does_not_create_new_artist_comment(self):
        # Arrange
        user = factories.UserFactory()
        song = song_factories.SongFactory(clean_title=self.old_title)
        artist_factories.ArtistFactory(user=user, profile=user.profile, songs=(song,))
        self.client.force_login(user)

        # Act
        response=self.client.post(reverse('song_details', kwargs={'pk': song.id}), {'text': ''})

        # Assert
        self.assertRedirects(response, reverse('view_song', kwargs = {'pk': song.id}))
        query_set = ArtistComment.objects.filter(song=song, profile=user.profile)
        self.assertEquals(0, len(query_set))

    def test_artist_only_creates_their_own_comment_to_song(self):
        # Arrange
        user = factories.UserFactory()
        user_2 = factories.UserFactory()
        song = song_factories.SongFactory(clean_title=self.old_title)
        artist_factories.ArtistFactory(user=user, profile=user.profile, songs=(song,))
        artist_factories.ArtistFactory(user=user_2, profile=user_2.profile, songs=(song,))
        self.client.force_login(user)

        # Act
        response=self.client.post(reverse('song_details', kwargs={'pk': song.id}), {'text': self.new_text})

        # Assert
        self.assertRedirects(response, reverse('view_song', kwargs = {'pk': song.id}))
        self.assertEquals(1, len(ArtistComment.objects.filter(song=song, profile=user.profile)))
        self.assertEquals(0, len(ArtistComment.objects.filter(song=song, profile=user_2.profile)))

    def test_artist_only_modifies_their_own_comment_to_song(self):
        # Arrange
        user = factories.UserFactory()
        user_2 = factories.UserFactory()
        song = song_factories.SongFactory(clean_title=self.old_title)
        artist_factories.ArtistFactory(user=user, profile=user.profile, songs=(song,))
        artist_factories.ArtistFactory(user=user_2, profile=user_2.profile, songs=(song,))
        song_factories.ArtistCommentFactory(profile=user.profile, song=song, text=self.old_text)
        song_factories.ArtistCommentFactory(profile=user_2.profile, song=song, text=self.old_text)
        self.client.force_login(user)

        # Act
        response=self.client.post(reverse('song_details', kwargs={'pk': song.id}), {'text': self.new_text})

        # Assert
        self.assertRedirects(response, reverse('view_song', kwargs = {'pk': song.id}))
        query_set_1 = ArtistComment.objects.filter(song=song, profile=user.profile)
        query_set_2 = ArtistComment.objects.filter(song=song, profile=user_2.profile)
        self.assertEquals(1, len(query_set_1))
        self.assertEquals(1, len(query_set_2))
        self.assertEquals(self.new_text, query_set_1[0].text)
        self.assertEquals(self.old_text, query_set_2[0].text)

    def test_artist_only_deletes_their_own_comment_to_song(self):
        # Arrange
        user = factories.UserFactory()
        user_2 = factories.UserFactory()
        song = song_factories.SongFactory(clean_title=self.old_title)
        artist_factories.ArtistFactory(user=user, profile=user.profile, songs=(song,))
        artist_factories.ArtistFactory(user=user_2, profile=user_2.profile, songs=(song,))
        song_factories.ArtistCommentFactory(profile=user.profile, song=song, text=self.old_text)
        song_factories.ArtistCommentFactory(profile=user_2.profile, song=song, text=self.old_text)
        self.client.force_login(user)

        # Act
        response=self.client.post(reverse('song_details', kwargs={'pk': song.id}), {'text': ''})

        # Assert
        self.assertRedirects(response, reverse('view_song', kwargs = {'pk': song.id}))
        query_set_1 = ArtistComment.objects.filter(song=song, profile=user.profile)
        query_set_2 = ArtistComment.objects.filter(song=song, profile=user_2.profile)
        self.assertEquals(0, len(query_set_1))
        self.assertEquals(1, len(query_set_2))

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
        self.assertTemplateUsed(response, 'browse_songs.html')

    def test_browse_by_filename_view_lists_correct_songs(self):
        response = self.client.get(reverse('browse_by_filename', kwargs={'query': 'f'}))
        self.assertEqual(response.status_code, 200)
        filtered_songs = list(filter(lambda song:song.filename[0]=="F", self.songs))
        self.assertCountEqual(list(response.context_data['songs']), filtered_songs)

    def test_browse_by_filename_view_lists_correct_songs_in_order(self):
        response = self.client.get(reverse('browse_by_filename', kwargs={'query': 'f'}))
        self.assertEqual(response.status_code, 200)
        filtered_songs = list(filter(lambda song:song.filename[0]=="F", self.songs))
        filtered_songs.sort(key=lambda song:song.filename)
        self.assertEqual(list(response.context_data['songs']), filtered_songs)

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
        self.assertTemplateUsed(response, 'browse_songs.html')

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
        for i in range(50):
            song_factories.SongFactory(license=Song.Licenses.SHARE_ALIKE)

        # Page 1
        response = self.client.get(reverse('browse_by_license', kwargs={'query': Song.Licenses.SHARE_ALIKE}) + "?page=1")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(40, len(response.context_data['songs']))

        # Page 2
        response = self.client.get(reverse('browse_by_license', kwargs={'query': Song.Licenses.SHARE_ALIKE}) + "?page=2")
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
        self.assertTemplateUsed(response, 'browse_songs.html')

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
        for i in range(50):
            song_factories.SongFactory(genre=Song.Genres.ALTERNATIVE_METAL)

        # Page 1
        response = self.client.get(reverse('browse_by_genre', kwargs={'query': Song.Genres.ALTERNATIVE_METAL}) + "?page=1")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(40, len(response.context_data['songs']))

        # Page 2
        response = self.client.get(reverse('browse_by_genre', kwargs={'query': Song.Genres.ALTERNATIVE_METAL}) + "?page=2")
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
        self.assertTemplateUsed(response, 'browse_songs.html')

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
        for i in range(50):
            song = song_factories.SongFactory()
            song_factories.SongStatsFactory(average_comment_score=10.0, song=song)

        # Page 1
        response = self.client.get(reverse('browse_by_rating', kwargs={'query': 9}) + "?page=1")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(40, len(response.context_data['songs']))

        # Page 2
        response = self.client.get(reverse('browse_by_rating', kwargs={'query': 9}) + "?page=2")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(10, len(response.context_data['songs']))

    def test_browse_by_rating_view_accepts_valid_query_params(self):
        for r in [9, 8, 7, 6, 5, 4, 3, 2, 1]:
            response = self.client.get(reverse('browse_by_rating', kwargs={'query': r}))
            self.assertEqual(response.status_code, 200)

    def test_browse_by_genre_view_rejects_invalid_query_params(self):
        response = self.client.get(reverse('browse_by_rating', kwargs={'query': 11}))
        self.assertRedirects(response, reverse('home'))

class UploadFormTests(TestCase):
    test_mod_filename = 'test1.mod'
    test_mod_zip_name = 'test1.mod.zip'
    test_it_filename = 'test2.it'
    test_it_zip_name = 'test2.it.zip'
    test_s3m_filename = 'test3.s3m'
    test_s3m_zip_name = 'test3.s3m.zip'

    def setUp(self):
        self.temp_upload_dir = settings.TEMP_UPLOAD_DIR
        self.new_file_dir = settings.NEW_FILE_DIR

    def tearDown(self):
        # Cleanup new_file_dir after each test
        for filename in os.listdir(self.new_file_dir):
            file_path = os.path.join(self.new_file_dir, filename)
            os.remove(file_path)
            
    def assert_zipped_file(self, new_file_dir, zipped_filename, unzipped_filename):
        # Verify that a zip file has been added 
        self.assertTrue(os.path.isfile(os.path.join(new_file_dir, zipped_filename)))

        # Open the zip file and get the list of files inside
        with zipfile.ZipFile(os.path.join(new_file_dir, zipped_filename), 'r') as zip_file:
            file_list = zip_file.namelist()

        # Verify that the zip file contains the original song
        self.assertEqual(len(file_list), 1)
        self.assertEqual(file_list[0], unzipped_filename)

    def assert_song_in_database(self, filename, title, format, channels, profile, is_by_uploader):
        new_song = NewSong.objects.get(filename=filename)
        self.assertEqual(title, new_song.title)
        self.assertEqual(format, new_song.format)
        self.assertEqual(channels, new_song.channels)    
        self.assertEqual(profile, new_song.uploader_profile)
        self.assertEqual(is_by_uploader, new_song.is_by_uploader)

    def assert_context_success(self, context, total_expected, filenames, titles, formats):
        self.assertIn('successful_files', context)
        successful_files = context['successful_files']
        self.assertEqual(len(successful_files), total_expected)

        for i in range(total_expected):
            successful_file = successful_files[i]
            self.assertEqual(successful_file['filename'], filenames[i])
            self.assertEqual(successful_file['title'], titles[i])
            self.assertEqual(successful_file['format'], formats[i])

    def test_upload_view_redirects_unauthenticated_user(self):
        # Arrange
        upload_url = reverse('upload_songs')
        login_url = reverse('login')

        # Act
        response = self.client.get(upload_url)

        # Assert
        self.assertRedirects(response, f"{login_url}?next={upload_url}")

    def test_upload_view_permits_authenticated_user(self):
        # Arrange
        user = factories.UserFactory()
        self.client.force_login(user)

        # Act
        response = self.client.get(reverse('upload_songs'))

        # Assert
        self.assertEquals(200, response.status_code)
        self.assertTemplateUsed(response, "upload.html")

    def test_upload_single_song(self):
        # Arrange
        user = factories.UserFactory()
        file_path = os.path.join(os.path.dirname(__file__), 'testdata', self.test_mod_filename)

        with open(file_path, 'rb') as f:
            file_data = f.read()
        uploaded_file = SimpleUploadedFile(self.test_mod_filename, file_data, content_type='application/octet-stream')

        self.client.force_login(user)

        # Act
        response = self.client.post(reverse('upload_songs'), {
            'written_by_me': 'yes',
            'song_file': uploaded_file
        })

        # Assert        
        self.assert_zipped_file(self.new_file_dir, self.test_mod_zip_name, self.test_mod_filename)
        self.assertEqual(os.listdir(self.temp_upload_dir), [])
        self.assert_song_in_database(self.test_mod_filename, 'Test Song', Song.Formats.MOD, 4, user.profile, True)
        self.assert_context_success(response.context, 1, [self.test_mod_filename], ['Test Song'], [Song.Formats.MOD])

    def test_upload_multiple_songs(self):
        # Arrange
        user = factories.UserFactory()
        self.client.force_login(user)

        mod_path = os.path.join(os.path.dirname(__file__), 'testdata', self.test_mod_filename)
        it_path = os.path.join(os.path.dirname(__file__), 'testdata', self.test_it_filename)
        s3m_path = os.path.join(os.path.dirname(__file__), 'testdata', self.test_s3m_filename)

        with tempfile.TemporaryDirectory() as temp_dir:
            zip_file_path = os.path.join(temp_dir, 'test.zip')

            with zipfile.ZipFile(zip_file_path, 'w') as zip_file:
                zip_file.write(mod_path, arcname=self.test_mod_filename)
                zip_file.write(it_path, arcname=self.test_it_filename)
                zip_file.write(s3m_path, arcname=self.test_s3m_filename)

            # Act
            with open(zip_file_path, 'rb') as f:
                response = self.client.post(reverse('upload_songs'), {'written_by_me': 'no', 'song_file': f})

            # Assert
            self.assert_zipped_file(self.new_file_dir, self.test_mod_zip_name, self.test_mod_filename)
            self.assert_zipped_file(self.new_file_dir, self.test_it_zip_name, self.test_it_filename)
            self.assert_zipped_file(self.new_file_dir, self.test_s3m_zip_name, self.test_s3m_filename)

            self.assertEqual(len(os.listdir(self.temp_upload_dir)), 0)

            self.assert_song_in_database(self.test_mod_filename, 'Test Song', Song.Formats.MOD, 4, user.profile, False)
            self.assert_song_in_database(self.test_it_filename, 'Test IT', Song.Formats.IT, 32, user.profile, False)
            self.assert_song_in_database(self.test_s3m_filename, 'Test S3M', Song.Formats.S3M, 16, user.profile, False)

            self.assert_context_success(response.context, 3, [self.test_mod_filename, self.test_it_filename, self.test_s3m_filename], ['Test Song', 'Test IT', 'Test S3M'], [Song.Formats.MOD, Song.Formats.IT, Song.Formats.S3M])

    def test_reject_files_already_in_screening(self):
        # Arrange
        user = factories.UserFactory()
        file_path = os.path.join(os.path.dirname(__file__), 'testdata', self.test_mod_filename)

        song_factories.NewSongFactory(hash='47c9d81e6c4966913e068a84b1b340f6', uploader_profile=user.profile)

        with open(file_path, 'rb') as f:
            file_data = f.read()
        uploaded_file = SimpleUploadedFile(self.test_mod_filename, file_data, content_type='application/octet-stream')

        self.client.force_login(user)

        # Act
        response = self.client.post(reverse('upload_songs'), {
            'written_by_me': 'yes',
            'song_file': uploaded_file
        })

        # Assert
        self.assertFalse(os.path.isfile(os.path.join(self.new_file_dir, self.test_mod_filename)))
        
        self.assertIn('successful_files', response.context)
        successful_files = response.context['successful_files']
        self.assertEqual(len(successful_files), 0)

        self.assertIn('failed_files', response.context)
        failed_files = response.context['failed_files']
        self.assertEqual(len(failed_files), 1)
        failed_file = failed_files[0]
        self.assertEqual(failed_file['filename'], self.test_mod_filename)
        self.assertEqual(failed_file['reason'], 'An identical song was already found in the upload processing queue.')

    def test_reject_files_already_in_archive(self):
        # Arrange
        user = factories.UserFactory()
        file_path = os.path.join(os.path.dirname(__file__), 'testdata', self.test_mod_filename)

        song_factories.SongFactory(hash='47c9d81e6c4966913e068a84b1b340f6')

        with open(file_path, 'rb') as f:
            file_data = f.read()
        uploaded_file = SimpleUploadedFile(self.test_mod_filename, file_data, content_type='application/octet-stream')

        self.client.force_login(user)

        # Act
        response = self.client.post(reverse('upload_songs'), {
            'written_by_me': 'yes',
            'song_file': uploaded_file
        })

        # Assert
        self.assertFalse(os.path.isfile(os.path.join(self.new_file_dir, self.test_mod_filename)))
        
        self.assertIn('successful_files', response.context)
        successful_files = response.context['successful_files']
        self.assertEqual(len(successful_files), 0)

        self.assertIn('failed_files', response.context)
        failed_files = response.context['failed_files']
        self.assertEqual(len(failed_files), 1)
        failed_file = failed_files[0]
        self.assertEqual(failed_file['filename'], self.test_mod_filename)
        self.assertEqual(failed_file['reason'], 'An identical song was already found in the archive.')

    @override_settings(MAXIMUM_UPLOAD_SIZE=1000)
    def test_reject_files_that_are_too_large(self):
        # Arrange
        user = factories.UserFactory()
        file_path = os.path.join(os.path.dirname(__file__), 'testdata', self.test_mod_filename)

        with open(file_path, 'rb') as f:
            file_data = f.read()
        uploaded_file = SimpleUploadedFile(self.test_mod_filename, file_data, content_type='application/octet-stream')

        self.client.force_login(user)

        # Act
        response = self.client.post(reverse('upload_songs'), {
            'written_by_me': 'yes',
            'song_file': uploaded_file
        })

        # Assert
        self.assertFalse(os.path.isfile(os.path.join(self.new_file_dir, self.test_mod_filename)))

        self.assertIn('successful_files', response.context)
        successful_files = response.context['successful_files']
        self.assertEqual(len(successful_files), 0)

        self.assertIn('failed_files', response.context)
        failed_files = response.context['failed_files']
        self.assertEqual(len(failed_files), 1)
        failed_file = failed_files[0]
        self.assertEqual(failed_file['filename'], self.test_mod_filename)
        self.assertEqual(failed_file['reason'], f'The file was above the maximum allowed size of {settings.MAXIMUM_UPLOAD_SIZE} bytes.')

    @override_settings(MAXIMUM_UPLOAD_FILENAME_LENGTH=4)
    def test_reject_file_with_long_filename(self):
        # Arrange
        user = factories.UserFactory()
        file_path = os.path.join(os.path.dirname(__file__), 'testdata', self.test_mod_filename)

        with open(file_path, 'rb') as f:
            file_data = f.read()
        uploaded_file = SimpleUploadedFile(self.test_mod_filename, file_data, content_type='application/octet-stream')

        self.client.force_login(user)

        # Act
        response = self.client.post(reverse('upload_songs'), {
            'written_by_me': 'yes',
            'song_file': uploaded_file
        })

        # Assert
        self.assertFalse(os.path.isfile(os.path.join(self.new_file_dir, self.test_mod_filename)))

        self.assertIn('successful_files', response.context)
        successful_files = response.context['successful_files']
        self.assertEqual(len(successful_files), 0)

        self.assertIn('failed_files', response.context)
        failed_files = response.context['failed_files']
        self.assertEqual(len(failed_files), 1)
        failed_file = failed_files[0]
        self.assertEqual(failed_file['filename'], self.test_mod_filename)
        self.assertEqual(failed_file['reason'], f'The filename length was above the maximum allowed limit of {settings.MAXIMUM_UPLOAD_FILENAME_LENGTH} characters.')

    def test_reject_file_when_modinfo_fails(self):
        # Arrange
        user = factories.UserFactory()
        file_path = os.path.join(os.path.dirname(__file__), 'testdata', 'not_a_mod.txt')

        with open(file_path, 'rb') as f:
            file_data = f.read()
        uploaded_file = SimpleUploadedFile('not_a_mod.txt', file_data, content_type='application/octet-stream')

        self.client.force_login(user)

        # Act
        response = self.client.post(reverse('upload_songs'), {
            'written_by_me': 'yes',
            'song_file': uploaded_file
        })

        # Assert
        self.assertFalse(os.path.isfile(os.path.join(self.new_file_dir, 'not_a_mod.txt')))

        self.assertIn('successful_files', response.context)
        successful_files = response.context['successful_files']
        self.assertEqual(len(successful_files), 0)

        self.assertIn('failed_files', response.context)
        failed_files = response.context['failed_files']
        self.assertEqual(len(failed_files), 1)
        failed_file = failed_files[0]
        self.assertEqual(failed_file['filename'], 'not_a_mod.txt')
        self.assertEqual(failed_file['reason'], f'Did not recognize this file as a valid mod format.')

    @override_settings(UNSUPPORTED_FORMATS=['it'])
    def test_reject_file_if_format_not_supported(self):
        # Arrange
        user = factories.UserFactory()
        file_path = os.path.join(os.path.dirname(__file__), 'testdata', self.test_it_filename)

        with open(file_path, 'rb') as f:
            file_data = f.read()
        uploaded_file = SimpleUploadedFile(self.test_it_filename, file_data, content_type='application/octet-stream')

        self.client.force_login(user)

        # Act
        response = self.client.post(reverse('upload_songs'), {
            'written_by_me': 'yes',
            'song_file': uploaded_file
        })

        # Assert
        self.assertFalse(os.path.isfile(os.path.join(self.new_file_dir, self.test_it_filename)))

        self.assertIn('successful_files', response.context)
        successful_files = response.context['successful_files']
        self.assertEqual(len(successful_files), 0)

        self.assertIn('failed_files', response.context)
        failed_files = response.context['failed_files']
        self.assertEqual(len(failed_files), 1)
        failed_file = failed_files[0]
        self.assertEqual(failed_file['filename'], self.test_it_filename)
        self.assertEqual(failed_file['reason'], 'This format is not currently supported.')

    def test_rename_file_extension_when_it_does_not_match_the_format(self):
        # Arrange
        user = factories.UserFactory()
        file_path = os.path.join(os.path.dirname(__file__), 'testdata', self.test_mod_filename)

        with open(file_path, 'rb') as f:
            file_data = f.read()
        uploaded_file = SimpleUploadedFile('test1.xm', file_data, content_type='application/octet-stream')

        self.client.force_login(user)

        # Act
        response = self.client.post(reverse('upload_songs'), {
            'written_by_me': 'yes',
            'song_file': uploaded_file
        })

        # Assert        
        self.assert_zipped_file(self.new_file_dir, self.test_mod_zip_name, self.test_mod_filename)
        self.assertEqual(os.listdir(self.temp_upload_dir), [])
        self.assert_song_in_database(self.test_mod_filename, 'Test Song', Song.Formats.MOD, 4, user.profile, True)
        self.assert_context_success(response.context, 1, [self.test_mod_filename], ['Test Song'], [Song.Formats.MOD])

    def test_rename_file_to_remove_whitespace_and_uppercase_letters(self):
        # Arrange
        user = factories.UserFactory()
        file_path = os.path.join(os.path.dirname(__file__), 'testdata', self.test_mod_filename)

        with open(file_path, 'rb') as f:
            file_data = f.read()
        uploaded_file = SimpleUploadedFile('Test  1.mod', file_data, content_type='application/octet-stream')

        self.client.force_login(user)

        # Act
        response = self.client.post(reverse('upload_songs'), {
            'written_by_me': 'yes',
            'song_file': uploaded_file
        })

        # Assert        
        self.assert_zipped_file(self.new_file_dir, 'test_1.mod.zip', 'test_1.mod')
        self.assertEqual(os.listdir(self.temp_upload_dir), [])
        self.assert_song_in_database('test_1.mod', 'Test Song', Song.Formats.MOD, 4, user.profile, True)
        self.assert_context_success(response.context, 1, ['test_1.mod'], ['Test Song'], [Song.Formats.MOD])

class PendingUploadsViewTest(TestCase):
    def test_pending_uploads_view_redirects_unauthenticated_user(self):
        # Arrange
        upload_url = reverse('pending_uploads')
        login_url = reverse('login')

        # Act
        response = self.client.get(upload_url)

        # Assert
        self.assertRedirects(response, f"{login_url}?next={upload_url}")

    def test_pending_uploads_view_permits_authenticated_user(self):
        # Arrange
        user = factories.UserFactory()
        self.client.force_login(user)

        # Act
        response = self.client.get(reverse('pending_uploads'))

        # Assert
        self.assertEquals(200, response.status_code)
        self.assertTemplateUsed(response, "pending_uploads.html")

    def test_only_retrieves_pending_uploads_for_authenticated_user(self):
        # Arrange
        user = factories.UserFactory()
        user_2 = factories.UserFactory()
        self.client.force_login(user)

        song_1 = song_factories.NewSongFactory(filename='song1.mod', uploader_profile=user.profile)
        song_2 = song_factories.NewSongFactory(filename='song2.mod', uploader_profile=user.profile)
        song_3 = song_factories.NewSongFactory(filename='song3.mod', uploader_profile=user_2.profile)

        # Act
        response = self.client.get(reverse('pending_uploads'))

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pending_uploads.html')
        self.assertQuerysetEqual(
            response.context['pending_uploads'],
            [repr(song_1), repr(song_2)],
            ordered=False
        )
        self.assertNotIn(repr(song_3), response.content.decode())