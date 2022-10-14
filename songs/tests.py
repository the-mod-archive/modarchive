from django.test import TestCase
from django.urls.base import reverse
from unittest.mock import patch

from artists import factories as artist_factories
from homepage.tests import factories
from songs.models import ArtistComment, Favorite, Song
from songs.templatetags import filters
from songs import factories as song_factories

class SongModelTests(TestCase):
    def test_gets_clean_title_when_available(self):
        song = Song(title="song title", clean_title="Song Title")
        self.assertEqual("Song Title", song.get_title())

    def test_gets_original_title_when_no_clean_title_available(self):
        song = Song(title="song title")
        self.assertEqual("song title", song.get_title())

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
        song = song_factories.SongFactory(genre_id=1)
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
        response = self.client.post(reverse('add_comment', kwargs={'pk': song.id}), {'rating': 10, 'text': "This is my review", 'genre': 1})

        # Assert
        self.assertRedirects(response, reverse('view_song', kwargs = {'pk': song.id}))
        song.refresh_from_db()
        self.assertEquals(1, song.genre_id)

    def test_post_cannot_change_genre_if_already_set_in_song(self):
        # Arrange
        user = factories.UserFactory()
        song = song_factories.SongFactory(genre_id=1)
        self.client.force_login(user)

        # Act
        response = self.client.post(reverse('add_comment', kwargs={'pk': song.id}), {'rating': 10, 'text': "This is my review", 'genre': 1})

        # Assert
        self.assertRedirects(response, reverse('view_song', kwargs = {'pk': song.id}))
        song.refresh_from_db()
        self.assertEquals(1, song.genre_id)

    def test_post_leaving_genre_blank_does_not_set_genre_to_blank(self):
        # Arrange
        user = factories.UserFactory()
        song = song_factories.SongFactory(genre_id=1)
        self.client.force_login(user)

        # Act
        response = self.client.post(reverse('add_comment', kwargs={'pk': song.id}), {'rating': 10, 'text': "This is my review"})

        # Assert
        self.assertRedirects(response, reverse('view_song', kwargs = {'pk': song.id}))
        song.refresh_from_db()
        self.assertEquals(1, song.genre_id)

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
        genre = song_factories.GenreFactory()

        update_song_details_url = reverse('song_details', kwargs={'pk': song.id})
        login_url = reverse('login')

        # GET test
        response=self.client.get(update_song_details_url)
        self.assertRedirects(response, f"{login_url}?next={update_song_details_url}")

        # POST test
        response=self.client.post(update_song_details_url, {'genre_id': genre.id})
        self.assertRedirects(response, f"{login_url}?next={update_song_details_url}")

    def test_cannot_update_details_of_somebody_elses_song(self):
        # Arrange
        user = factories.UserFactory()
        user_2 = factories.UserFactory()
        song = song_factories.SongFactory(clean_title=self.old_title)
        artist_factories.ArtistFactory(user=user, profile=user.profile)
        artist_factories.ArtistFactory(user=user_2, profile=user_2.profile, songs=(song,))
        genre = song_factories.GenreFactory()
        self.client.force_login(user)

        # GET test
        response=self.client.get(reverse('song_details', kwargs={'pk': song.id}))
        self.assertRedirects(response, reverse('view_song', kwargs = {'pk': song.id}))

        # POST test
        response=self.client.post(reverse('song_details', kwargs={'pk': song.id}), {'genre': genre.id, 'clean_title': self.new_title})
        self.assertRedirects(response, reverse('view_song', kwargs = {'pk': song.id}))
        song.refresh_from_db()
        self.assertEquals(None, song.genre)
        self.assertEquals(self.old_title, song.clean_title)

    def test_happy_path_updates_all_fields(self):
        # Arrange
        user = factories.UserFactory()
        song = song_factories.SongFactory(clean_title=self.old_title)
        artist_factories.ArtistFactory(user=user, profile=user.profile, songs=(song,))
        genre = song_factories.GenreFactory()
        comment = song_factories.ArtistCommentFactory(profile=user.profile, song=song, text=self.old_text)
        self.client.force_login(user)

        # GET test
        response=self.client.get(reverse('song_details', kwargs={'pk': song.id}))
        self.assertTemplateUsed(response, 'update_song_details.html')
        self.assertEquals(song, response.context['object'])
        
        # POST test
        response=self.client.post(reverse('song_details', kwargs={'pk': song.id}), {'genre': genre.id, 'clean_title': self.new_title, 'text': self.new_text})
        self.assertRedirects(response, reverse('view_song', kwargs = {'pk': song.id}))
        song.refresh_from_db()
        self.assertEquals(self.new_title, song.clean_title)
        self.assertEquals(genre, song.genre)
        comment.refresh_from_db()
        self.assertEquals(self.new_text, comment.text)

    def test_adding_text_creates_new_artist_comment(self):
        # Arrange
        user = factories.UserFactory()
        song = song_factories.SongFactory(clean_title=self.old_title)
        artist_factories.ArtistFactory(user=user, profile=user.profile, songs=(song,))
        genre = song_factories.GenreFactory()
        self.client.force_login(user)
        
        # Act
        response=self.client.post(reverse('song_details', kwargs={'pk': song.id}), {'genre': genre.id, 'text': self.new_text})

        # Assert
        self.assertRedirects(response, reverse('view_song', kwargs = {'pk': song.id}))
        song.refresh_from_db()
        self.assertEquals(genre, song.genre)
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