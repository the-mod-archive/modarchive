from django.test import TestCase
from django.urls.base import reverse

from homepage.tests import factories
from songs.models import Song
from songs.templatetags import filters

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
        song = factories.SongFactory()
        factories.ArtistFactory(songs=(song,), user=user, profile=user.profile)

        self.assertFalse(song.can_user_leave_comment(user.profile.id))

    def test_cannot_leave_comment_if_already_commented(self):
        user = factories.UserFactory()
        song = factories.SongFactory()
        factories.CommentFactory(song=song, profile=user.profile)
        
        self.assertFalse(song.can_user_leave_comment(user.profile.id))

class CommentModelTests(TestCase):
    def test_song_stats_updated_correctly_after_removing_comment(self):
        song = factories.SongFactory()
        factories.SongStatsFactory(song=song)
        comment_1 = factories.CommentFactory(song=song, rating=10)
        comment_2 = factories.CommentFactory(song=song, rating=5)

        self.assertEquals(2, song.songstats.total_comments)
        self.assertEquals(7.5, song.songstats.average_comment_score)

        comment_1.delete()
        
        self.assertEquals(1, song.songstats.total_comments)
        self.assertEquals(5.0, song.songstats.average_comment_score)

    def test_song_stats_updated_correctly_after_removing_final_comment(self):
        song = factories.SongFactory()
        factories.SongStatsFactory(song=song)
        comment_1 = factories.CommentFactory(song=song, rating=10)

        comment_1.delete()

        self.assertEquals(0, song.songstats.total_comments)
        self.assertEquals(0.0, song.songstats.average_comment_score)

class SongListTests(TestCase):
    fixtures = ["songs.json"]

    def test_song_list_view_contains_all_songs(self):
        # Arrange
        expected_length = 33
        
        # Act
        response = self.client.get(reverse('songs'))
        
        # Assert
        actual_length = len(response.context['object_list'])
        
        self.assertTemplateUsed(response, 'song_list.html')
        self.assertTrue('object_list' in response.context)
        self.assertEqual(expected_length, actual_length, f"Expected {expected_length} objects in songs list but got {actual_length}")

class ViewSongTests(TestCase):
    def test_context_contains_song_and_comments(self):
        song = factories.SongFactory(filename="file2.s3m", title="File 2", songstats=factories.SongStatsFactory())
        response = self.client.get(reverse('view_song', kwargs = {'pk': song.id}))
        factories.CommentFactory(song=song, rating=10, text="This was definitely a song!")
        factories.CommentFactory(song=song, rating=5, text="I disagree, this was not a song.")

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
        song = factories.SongFactory(filename="file2.s3m", title="File 2", songstats=factories.SongStatsFactory())
        
        # Act
        response = self.client.get(reverse('view_song', kwargs = {'pk': song.id}))

        # Assert
        self.assertFalse('can_comment' in response.context)

    def test_user_can_comment_if_has_not_commented(self):
        # Arrange
        user = factories.UserFactory()
        song = factories.SongFactory()
        self.client.force_login(user)
        
        # Act
        response = self.client.get(reverse('view_song', kwargs = {'pk': song.id}))

        # Assert
        self.assertTrue(response.context['can_comment'])

    def test_user_cannot_comment_if_has_already_commented(self):
        # Arrange
        user = factories.UserFactory()
        song = factories.SongFactory()
        factories.CommentFactory(song=song, profile=user.profile, rating=10, text="This was definitely a song!")
        self.client.force_login(user)

        # Act
        response = self.client.get(reverse('view_song', kwargs = {'pk': song.id}))

        # Assert
        self.assertFalse(response.context['can_comment'])
        

    def test_user_can_comment_when_not_the_song_composer(self):
        # Arrange
        user = factories.UserFactory()
        song = factories.SongFactory()
        artist = factories.ArtistFactory(songs=(song,))
        self.client.force_login(user)

        # Act
        response = self.client.get(reverse('view_song', kwargs = {'pk': song.id}))

        # Assert
        self.assertTrue(response.context['can_comment'])

    def test_user_cannot_comment_if_is_song_composer(self):
        # Arrange
        user = factories.UserFactory()
        song = factories.SongFactory()
        artist = factories.ArtistFactory(songs=(song,), profile=user.profile)
        self.client.force_login(user)

        # Act
        response = self.client.get(reverse('view_song', kwargs = {'pk': song.id}))

        # Assert
        self.assertFalse(response.context['can_comment'])

class DownloadTests(TestCase):
    fixtures = ["songs.json"]

    def test_download_redirects_to_external_url(self):
        # Arrange
        song = Song.objects.get(pk = 1)

        # Act
        response = self.client.get(f"/songs/{song.id}/download")

        # Assert
        self.assertRedirects(response, f"https://api.modarchive.org/downloads.php?moduleid={song.legacy_id}#{song.filename}", fetch_redirect_response=False)

    def test_download_increases_download_count(self):
        # Arrange
        song = Song.objects.get(pk = 1)
        expected_download_count = song.songstats.downloads + 1

        # Act
        self.client.get(f"/songs/{song.id}/download")
        song.refresh_from_db()

        # Assert
        self.assertEquals(expected_download_count, song.songstats.downloads)

    def test_returns_404_if_song_id_is_missing(self):
        # Act
        response = self.client.get("/songs/1000/download")
        
        # Assert
        self.assertEqual(response.status_code, 404)

class AddCommentTests(TestCase):
    def test_get_add_comment_page_happy_path(self):
        # Arrange
        user = factories.UserFactory()
        song = factories.SongFactory()
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
        song = factories.SongFactory()
        self.client.force_login(user)

        # Act
        response = self.client.post(reverse('add_comment', kwargs={'pk': song.id}), {'rating': 10, 'text': "This is my review"})

        # Assert
        self.assertRedirects(response, reverse('view_song', kwargs = {'pk': song.id}))
        self.assertEquals(1, len(song.comment_set.all()))

    def test_post_add_comment_calculates_stats_correctly(self):
        # Arrange
        user = factories.UserFactory()
        song = factories.SongFactory()
        factories.SongStatsFactory(song=song)
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
        song = factories.SongFactory()
        factories.SongStatsFactory(song=song)
        factories.CommentFactory(song=song, rating=5, text='some review')
        self.client.force_login(user)

        # Act
        self.client.post(reverse('add_comment', kwargs={'pk': song.id}), {'rating': 10, 'text': "This is my review"})

        # Assert
        song.refresh_from_db()
        self.assertEquals(2, len(song.comment_set.all()))
        self.assertEquals(2, song.songstats.total_comments)
        self.assertEquals(7.5, song.songstats.average_comment_score)

    def test_get_user_redirected_for_own_song(self):
        # Arrange
        user = factories.UserFactory()
        song = factories.SongFactory()
        artist = factories.ArtistFactory(user=user, profile=user.profile, songs=(song,))
        self.client.force_login(user)

        # Act
        response = self.client.get(reverse('add_comment', kwargs={'pk': song.id}))

        # Assert
        self.assertRedirects(response, reverse('view_song', kwargs = {'pk': song.id}))

    def test_post_user_redirected_for_own_song(self):
        # Arrange
        user = factories.UserFactory()
        song = factories.SongFactory()
        artist = factories.ArtistFactory(user=user, profile=user.profile, songs=(song,))
        self.client.force_login(user)

        # Act
        response = self.client.post(reverse('add_comment', kwargs={'pk': song.id}), {'rating': 10, 'text': "This is my review"})

        # Assert
        self.assertRedirects(response, reverse('view_song', kwargs = {'pk': song.id}))
        self.assertEquals(0, Song.objects.get(id=song.id).comment_set.all().count())

    def test_get_user_redirected_when_already_commented(self):
        # Arrange
        user = factories.UserFactory()
        song = factories.SongFactory()
        comment = factories.CommentFactory(profile=user.profile, song=song)
        self.client.force_login(user)

        # Act
        response = self.client.get(reverse('add_comment', kwargs={'pk': song.id}))

        # Assert
        self.assertRedirects(response, reverse('view_song', kwargs = {'pk': song.id}))

    def test_post_user_redirected_when_already_commented(self):
        # Arrange
        user = factories.UserFactory()
        song = factories.SongFactory()
        comment = factories.CommentFactory(profile=user.profile, song=song)
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