from django.test import TestCase
from django.urls import reverse

from django.contrib.auth.models import Permission
from artists.factories import ArtistFactory
from homepage.tests.factories import UserFactory
from interactions.factories import CommentFactory
from songs.factories import SongFactory, SongStatsFactory
from songs.models import Song

class AddCommentTests(TestCase):
    REVIEW_TEXT = "This is my review"

    def test_get_add_comment_page_happy_path(self):
        # Arrange
        user = UserFactory(permissions=[Permission.objects.get(codename='add_comment')])
        song = SongFactory()
        self.client.force_login(user)

        # Act
        response = self.client.get(reverse('add_comment', kwargs={'pk': song.id}))

        # Assert
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, "add_comment.html")
        self.assertEqual(song.id, response.context['song'].id)
        self.assertEqual(song.title, response.context['song'].get_title())

    def test_post_add_comment_happy_path(self):
        # Arrange
        user = UserFactory(permissions=[Permission.objects.get(codename='add_comment')])
        song = SongFactory()
        self.client.force_login(user)

        # Act
        response = self.client.post(
            reverse('add_comment', kwargs={'pk': song.id}), {'rating': 10, 'text': self.REVIEW_TEXT}
        )

        # Assert
        self.assertRedirects(response, reverse('view_song', kwargs = {'pk': song.id}))
        self.assertEqual(1, len(song.comment_set.all()))

    def test_cannot_get_comment_page_without_permission(self):
        # Arrange
        user = UserFactory()
        self.client.force_login(user)
        song = SongFactory()

        # Act
        response = self.client.get(reverse('add_comment', kwargs={'pk': song.id}))

        # Assert
        self.assertEqual(403, response.status_code)

    def test_cannot_post_comment_without_permission(self):
        # Arrange
        user = UserFactory()
        self.client.force_login(user)
        song = SongFactory()

        # Act
        response = self.client.post(
            reverse('add_comment', kwargs={'pk': song.id}), {'rating': 10, 'text': self.REVIEW_TEXT}
        )

        # Assert
        self.assertEqual(403, response.status_code)

    def test_post_add_comment_calculates_stats_correctly(self):
        # Arrange
        user = UserFactory(permissions=[Permission.objects.get(codename='add_comment')])
        song = SongFactory()
        SongStatsFactory(song=song)
        self.client.force_login(user)

        # Act
        self.client.post(
            reverse('add_comment', kwargs={'pk': song.id}), {'rating': 10, 'text': self.REVIEW_TEXT}
        )

        # Assert
        song.refresh_from_db()
        self.assertEqual(1, len(song.comment_set.all()))
        self.assertEqual(1, song.songstats.total_comments)
        self.assertEqual(10.0, song.songstats.average_comment_score)

    def test_post_add_comment_calculates_stats_correctly_with_existing_comments(self):
        # Arrange
        user = UserFactory(permissions=[Permission.objects.get(codename='add_comment')])
        song = SongFactory()
        SongStatsFactory(song=song)
        CommentFactory(song=song, rating=5, text='some review')
        self.client.force_login(user)

        # Act
        self.client.post(
            reverse('add_comment', kwargs={'pk': song.id}), {'rating': 10, 'text': self.REVIEW_TEXT}
        )

        # Assert
        song.refresh_from_db()
        self.assertEqual(2, len(song.comment_set.all()))
        self.assertEqual(2, song.songstats.total_comments)
        self.assertEqual(7.5, song.songstats.average_comment_score)

    def test_post_add_comment_calculates_stats_correctly_when_stats_object_not_created_yet(self):
        # Arrange
        user = UserFactory(permissions=[Permission.objects.get(codename='add_comment')])
        song = SongFactory()
        self.client.force_login(user)

        # Act
        self.client.post(
            reverse('add_comment', kwargs={'pk': song.id}), {'rating': 10, 'text': self.REVIEW_TEXT}
        )

        # Assert
        song.refresh_from_db()
        self.assertEqual(1, len(song.comment_set.all()))
        self.assertEqual(1, song.songstats.total_comments)
        self.assertEqual(10.0, song.songstats.average_comment_score)

    def test_get_user_redirected_for_own_song(self):
        # Arrange
        user = UserFactory(permissions=[Permission.objects.get(codename='add_comment')])
        song = SongFactory()
        ArtistFactory(user=user, profile=user.profile, songs=(song,))
        self.client.force_login(user)

        # Act
        response = self.client.get(reverse('add_comment', kwargs={'pk': song.id}))

        # Assert
        self.assertRedirects(response, reverse('view_song', kwargs = {'pk': song.id}))

    def test_post_user_redirected_for_own_song(self):
        # Arrange
        user = UserFactory(permissions=[Permission.objects.get(codename='add_comment')])
        song = SongFactory()
        ArtistFactory(user=user, profile=user.profile, songs=(song,))
        self.client.force_login(user)

        # Act
        response = self.client.post(
            reverse('add_comment', kwargs={'pk': song.id}), {'rating': 10, 'text': self.REVIEW_TEXT}
        )

        # Assert
        self.assertRedirects(response, reverse('view_song', kwargs = {'pk': song.id}))
        self.assertEqual(0, Song.objects.get(id=song.id).comment_set.all().count())

    def test_get_user_redirected_when_already_commented(self):
        # Arrange
        user = UserFactory(permissions=[Permission.objects.get(codename='add_comment')])
        song = SongFactory()
        CommentFactory(profile=user.profile, song=song)
        self.client.force_login(user)

        # Act
        response = self.client.get(reverse('add_comment', kwargs={'pk': song.id}))

        # Assert
        self.assertRedirects(response, reverse('view_song', kwargs = {'pk': song.id}))

    def test_post_user_redirected_when_already_commented(self):
        # Arrange
        user = UserFactory(permissions=[Permission.objects.get(codename='add_comment')])
        song = SongFactory()
        CommentFactory(profile=user.profile, song=song)
        self.client.force_login(user)

        # Act
        response = self.client.post(
            reverse('add_comment', kwargs={'pk': song.id}), {'rating': 10, 'text': self.REVIEW_TEXT}
        )

        # Assert
        self.assertRedirects(response, reverse('view_song', kwargs = {'pk': song.id}))
        self.assertEqual(1, Song.objects.get(id=song.id).comment_set.all().count())

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
        response = self.client.post(add_comment_url, {'rating': 10, 'text': self.REVIEW_TEXT})

        # Assert
        self.assertRedirects(response, f"{login_url}?next={add_comment_url}")

    def test_genre_form_available_when_song_has_no_genre(self):
        # Arrange
        user = UserFactory(permissions=[Permission.objects.get(codename='add_comment')])
        song = SongFactory()
        self.client.force_login(user)

        # Act
        response = self.client.get(reverse('add_comment', kwargs={'pk': song.id}))

        # Assert
        self.assertTrue(response.context.get('song_form'))
        self.assertTrue(response.context['song_form'].fields.get('genre'))

    def test_genre_form_not_available_when_song_has_genre(self):
        # Arrange
        user = UserFactory(permissions=[Permission.objects.get(codename='add_comment')])
        song = SongFactory(genre=Song.Genres.ELECTRONIC_GENERAL)
        self.client.force_login(user)

        # Act
        response = self.client.get(reverse('add_comment', kwargs={'pk': song.id}))

        # Assert
        self.assertFalse(response.context.get('song_form'))

    def test_post_genre_adds_genre_to_song_when_not_already_set(self):
        # Arrange
        user = UserFactory(permissions=[Permission.objects.get(codename='add_comment')])
        song = SongFactory()
        self.client.force_login(user)

        # Act
        response = self.client.post(
            reverse(
                'add_comment',
                kwargs={'pk': song.id}),
                {'rating': 10, 'text': self.REVIEW_TEXT, 'genre': Song.Genres.ELECTRONIC_GENERAL}
        )

        # Assert
        self.assertRedirects(response, reverse('view_song', kwargs = {'pk': song.id}))
        song.refresh_from_db()
        self.assertEqual(Song.Genres.ELECTRONIC_GENERAL, song.genre)

    def test_post_cannot_change_genre_if_already_set_in_song(self):
        # Arrange
        user = UserFactory(permissions=[Permission.objects.get(codename='add_comment')])
        song = SongFactory(genre=Song.Genres.ELECTRONIC_GENERAL)
        self.client.force_login(user)

        # Act
        response = self.client.post(
            reverse(
                'add_comment',
                kwargs={'pk': song.id}),
                {'rating': 10, 'text': self.REVIEW_TEXT, 'genre': Song.Genres.ALTERNATIVE}
        )

        # Assert
        self.assertRedirects(response, reverse('view_song', kwargs = {'pk': song.id}))
        song.refresh_from_db()
        self.assertEqual(Song.Genres.ELECTRONIC_GENERAL, song.genre)

    def test_post_leaving_genre_blank_does_not_set_genre_to_blank(self):
        # Arrange
        user = UserFactory(permissions=[Permission.objects.get(codename='add_comment')])
        song = SongFactory(genre=Song.Genres.ELECTRONIC_GENERAL)
        self.client.force_login(user)

        # Act
        response = self.client.post(
            reverse('add_comment', kwargs={'pk': song.id}), {'rating': 10, 'text': self.REVIEW_TEXT}
        )

        # Assert
        self.assertRedirects(response, reverse('view_song', kwargs = {'pk': song.id}))
        song.refresh_from_db()
        self.assertEqual(Song.Genres.ELECTRONIC_GENERAL, song.genre)
