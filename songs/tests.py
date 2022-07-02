from django.test import TestCase
from django.urls.base import reverse
from django.contrib.auth.models import User

from songs.models import Song, Comment

class SongModelTests(TestCase):
    fixtures = ["songs_2.json"]
    
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
        song = Song.objects.get(id=3)
        self.assertFalse(song.can_user_leave_comment(1))

    def test_cannot_leave_comment_if_already_commented(self):
        song = Song.objects.get(id=2)
        self.assertFalse(song.can_user_leave_comment(1))

class CommentModelTests(TestCase):
    fixtures = ["songs_2.json"]

    def test_song_stats_updated_correctly_after_removing_comment(self):
        song = Song.objects.get(id=4)
        new_comment = Comment(profile=None, song=song, text="comment text", rating=10)
        new_comment.save()

        song.refresh_from_db()
        self.assertEquals(2, song.songstats.total_comments)
        self.assertEquals(7.5, song.songstats.average_comment_score)

        new_comment.delete()
        song.refresh_from_db()
        self.assertEquals(1, song.songstats.total_comments)
        self.assertEquals(5.0, song.songstats.average_comment_score)

    def test_song_stats_updated_correctly_after_removing_final_comment(self):
        song = Song.objects.get(id=4)

        comment_to_delete = song.comment_set.all()[0]
        comment_to_delete.delete()

        song.refresh_from_db()
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
    fixtures = ["songs_2.json"]
    def test_context_contains_song_and_comments(self):
        response = self.client.get(reverse('view_song', kwargs = {'pk': 2}))

        self.assertTrue('song' in response.context)
        song = response.context['song']
        self.assertEquals(2, song.id)
        self.assertEquals("file2.s3m", song.filename)
        self.assertEquals("File 2", song.get_title())
        self.assertEquals(2, len(song.comment_set.all()))
        self.assertEquals("This was definitely a song!", song.comment_set.all()[0].text)
        self.assertEquals("I disagree, this was not a song.", song.comment_set.all()[1].text)
        self.assertEquals(10, song.comment_set.all()[0].rating)
        self.assertEquals(5, song.comment_set.all()[1].rating)


    def test_unauthenticated_user_cannot_comment(self):
        # Act
        response = self.client.get(reverse('view_song', kwargs = {'pk': 1}))

        # Assert
        self.assertFalse('can_comment' in response.context)

    def test_user_can_comment_if_has_not_commented(self):
        # Arrange
        self.client.force_login(User.objects.get_or_create(username='test_user')[0])
        
        # Act
        response = self.client.get(reverse('view_song', kwargs = {'pk': 1}))

        # Assert
        self.assertTrue(response.context['can_comment'])

    def test_user_cannot_comment_if_has_already_commented(self):
        # Arrange
        self.client.force_login(User.objects.get_or_create(username='test_user')[0])

        # Act
        response = self.client.get(reverse('view_song', kwargs = {'pk': 2}))

        # Assert
        self.assertFalse(response.context['can_comment'])
        

    def test_user_can_comment_when_not_the_song_composer(self):
        # Arrange
        self.client.force_login(User.objects.get_or_create(username='test_user')[0])

        # Act
        response = self.client.get(reverse('view_song', kwargs = {'pk': 1}))

        # Assert
        self.assertTrue(response.context['can_comment'])

    def test_user_cannot_comment_if_is_song_composer(self):
        # Arrange
        self.client.force_login(User.objects.get_or_create(username='test_user')[0])

        # Act
        response = self.client.get(reverse('view_song', kwargs = {'pk': 3}))

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
    fixtures = ["songs_2.json"]

    def test_get_add_comment_page_happy_path(self):
        # Arrange
        self.client.force_login(User.objects.get_or_create(username='test_user')[0])

        # Act
        response = self.client.get(reverse('add_comment', kwargs={'pk': 1}))

        # Assert
        self.assertEquals(200, response.status_code)
        self.assertTemplateUsed(response, "add_comment.html")
        self.assertEquals(1, response.context['song'].id)
        self.assertEquals("File 1", response.context['song'].get_title())

    def test_post_add_comment_happy_path(self):
        # Arrange
        self.client.force_login(User.objects.get_or_create(username='test_user')[0])

        # Act
        response = self.client.post(reverse('add_comment', kwargs={'pk': 1}), {'rating': 10, 'text': "This is my review"})

        # Assert
        self.assertRedirects(response, reverse('view_song', kwargs = {'pk': 1}))
        song = Song.objects.get(id=1)
        self.assertEquals(1, len(song.comment_set.all()))

    def test_post_add_comment_calculates_stats_correctly(self):
        # Arrange
        self.client.force_login(User.objects.get_or_create(username='test_user')[0])

        # Act
        self.client.post(reverse('add_comment', kwargs={'pk': 1}), {'rating': 10, 'text': "This is my review"})

        # Assert
        song = Song.objects.get(id=1)
        self.assertEquals(1, len(song.comment_set.all()))
        self.assertEquals(1, song.songstats.total_comments)
        self.assertEquals(10.0, song.songstats.average_comment_score)

    def test_post_add_comment_calculates_stats_correctly_with_existing_comments(self):
        # Arrange
        self.client.force_login(User.objects.get_or_create(username='test_user')[0])

        # Act
        self.client.post(reverse('add_comment', kwargs={'pk': 4}), {'rating': 10, 'text': "This is my review"})

        # Assert
        song = Song.objects.get(id=4)
        self.assertEquals(2, len(song.comment_set.all()))
        self.assertEquals(2, song.songstats.total_comments)
        self.assertEquals(7.5, song.songstats.average_comment_score)

    def test_get_user_redirected_for_own_song(self):
        # Arrange
        self.client.force_login(User.objects.get_or_create(username='test_user')[0])

        # Act
        response = self.client.get(reverse('add_comment', kwargs={'pk': 3}))

        # Assert
        self.assertRedirects(response, reverse('view_song', kwargs = {'pk': 3}))

    def test_post_user_redirected_for_own_song(self):
        # Arrange
        self.client.force_login(User.objects.get_or_create(username='test_user')[0])

        # Act
        response = self.client.post(reverse('add_comment', kwargs={'pk': 3}), {'rating': 10, 'text': "This is my review"})

        # Assert
        self.assertRedirects(response, reverse('view_song', kwargs = {'pk': 3}))
        self.assertEquals(0, Song.objects.get(id=3).comment_set.all().count())

    def test_get_user_redirected_when_already_commented(self):
        # Arrange
        self.client.force_login(User.objects.get_or_create(username='test_user')[0])

        # Act
        response = self.client.get(reverse('add_comment', kwargs={'pk': 2}))

        # Assert
        self.assertRedirects(response, reverse('view_song', kwargs = {'pk': 2}))

    def test_post_user_redirected_when_already_commented(self):
        # Arrange
        self.client.force_login(User.objects.get_or_create(username='test_user')[0])

        # Act
        response = self.client.post(reverse('add_comment', kwargs={'pk': 2}), {'rating': 10, 'text': "This is my review"})

        # Assert
        self.assertRedirects(response, reverse('view_song', kwargs = {'pk': 2}))
        self.assertEquals(2, Song.objects.get(id=2).comment_set.all().count())

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