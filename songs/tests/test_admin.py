import datetime
import os
from django.test import TestCase
from django.urls import reverse
from django.conf import settings

from homepage.tests import factories
from songs import factories as song_factories
from songs import models
from artists import factories as artist_factories

class MergeSongValidationTests(TestCase):
    def setUp(self):
        self.user = factories.UserFactory(is_staff=True, is_superuser=True)
        self.client.force_login(self.user)

    def test_is_invalid_if_song_to_merge_into_does_not_exist(self):
        # Arrange
        song_to_be_merged = song_factories.SongFactory()

        # Act
        response = self.client.post(
            f"/admin/songs/song/{song_to_be_merged.id}/merge_song/",
            {"song_to_merge_into_id": 99999},
            follow=True
        )

        # Assert
        self.assertEqual(response.status_code, 404)

    def test_is_invalid_if_song_to_merge_into_is_same_as_song_to_merge_from(self):
        # Arrange
        song_to_be_merged = song_factories.SongFactory()

        # Act
        response = self.client.post(
            f"/admin/songs/song/{song_to_be_merged.id}/merge_song/",
            {"song_to_merge_into_id": song_to_be_merged.id},
            follow=True
        )

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "You cannot merge a song into itself.")

    def test_renders_finalize_details_when_form_is_valid(self):
        # Arrange
        song_to_be_merged = song_factories.SongFactory()
        song_to_merge_into = song_factories.SongFactory()

        # Act
        response = self.client.post(
            f"/admin/songs/song/{song_to_be_merged.id}/merge_song/",
            {"song_to_merge_into_id": song_to_merge_into.id},
            follow=True
        )

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["song_to_merge_from"], song_to_be_merged)
        self.assertEqual(response.context["song_to_merge_into"], song_to_merge_into)
        self.assertEqual(response.context["merge_song_form"].initial["song_to_merge_into_id"], song_to_merge_into.id)
        self.assertTrue(response.context["merge_song_form"].fields["commit"].initial)

class MergeSongTests(TestCase):
    change_song_page = "admin:songs_song_change"

    def setUp(self):
        self.user = factories.UserFactory(is_staff=True, is_superuser=True)
        self.client.force_login(self.user)

    def tearDown(self):
        for filename in os.listdir(settings.REMOVED_FILE_DIR):
            file_path = os.path.join(settings.REMOVED_FILE_DIR, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)

    def create_song_to_be_merged(self, featured_date=None, featured_by=None):
        is_featured = featured_date is not None and featured_by is not None
        song = song_factories.SongFactory(folder="T", filename="test.mod", hash="123", is_featured=is_featured, featured_date=featured_date, featured_by=featured_by)

        # Create a dummy file to represent the uploaded file
        format_directory = f'{settings.MAIN_ARCHIVE_DIR}/{song.format.upper()}'
        if not os.path.exists(format_directory):
            os.mkdir(format_directory)
        file_directory = f'{format_directory}/{song.folder}'
        if not os.path.exists(file_directory):
            os.mkdir(file_directory)
        file_path = f'{file_directory}/{song.filename}.zip'
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write('test')

        return song

    def test_performs_basic_merge(self):
        # Arrange
        song_to_be_merged = self.create_song_to_be_merged()
        song_factories.SongStatsFactory(song=song_to_be_merged, downloads=30)
        song_to_merge_into = song_factories.SongFactory()
        song_factories.SongStatsFactory(song=song_to_merge_into, downloads=20)

        # Act
        response = self.client.post(
            f"/admin/songs/song/{song_to_be_merged.id}/merge_song/",
            {"song_to_merge_into_id": song_to_merge_into.id, "commit": True},
            follow=True
        )

        # Assert
        self.assertRedirects(response, reverse(self.change_song_page, args=(song_to_merge_into.id,)))
        song_to_merge_into.refresh_from_db()
        self.assertEqual(song_to_merge_into.get_stats().downloads, 50)
        self.assertTrue(models.SongRedirect.objects.filter(old_song_id=song_to_be_merged.id, song_id=song_to_merge_into.id).exists())
        self.assertFalse(models.Song.objects.filter(pk=song_to_be_merged.id).exists())
        self.assertFalse(os.path.exists(song_to_be_merged.get_archive_path()))
        self.assertTrue(os.path.exists(f'{settings.REMOVED_FILE_DIR}/{song_to_be_merged.filename}.zip'))
        self.assertFalse(song_to_be_merged.artist_set.exists())
        self.assertTrue(models.RejectedSong.objects.filter(hash=song_to_be_merged.hash).exists())
        rejected = models.RejectedSong.objects.get(hash=song_to_be_merged.hash)
        self.assertEqual(rejected.reason, models.RejectedSong.Reasons.ALREADY_EXISTS)
        self.assertEqual(rejected.message, f'TIDY-UP MERGED. {song_to_be_merged.filename} already exists as {song_to_merge_into.filename} on the archive.')
        self.assertEqual(rejected.filename, song_to_be_merged.filename)
        self.assertEqual(rejected.hash, song_to_be_merged.hash)
        self.assertFalse(song_to_merge_into.is_featured)

    def test_merges_artists_from_old_song_into_merged_song(self):
        # Arrange
        song_to_be_merged = self.create_song_to_be_merged()
        song_to_merge_into = song_factories.SongFactory()
        artist = artist_factories.ArtistFactory(songs=(song_to_be_merged,))

        # Act
        response = self.client.post(
            f"/admin/songs/song/{song_to_be_merged.id}/merge_song/",
            {"song_to_merge_into_id": song_to_merge_into.id, "commit": True},
            follow=True
        )

        # Assert
        self.assertRedirects(response, reverse(self.change_song_page, args=(song_to_merge_into.id,)))
        song_to_merge_into.refresh_from_db()
        self.assertTrue(song_to_merge_into.artist_set.filter(pk=artist.pk).exists())

    def test_artists_in_existing_song_are_unaffected(self):
        # Arrange
        song_to_be_merged = self.create_song_to_be_merged()
        song_to_merge_into = song_factories.SongFactory()
        artist = artist_factories.ArtistFactory(songs=(song_to_merge_into,))

        # Act
        response = self.client.post(
            f"/admin/songs/song/{song_to_be_merged.id}/merge_song/",
            {"song_to_merge_into_id": song_to_merge_into.id, "commit": True},
            follow=True
        )

        # Assert
        self.assertRedirects(response, reverse(self.change_song_page, args=(song_to_merge_into.id,)))
        song_to_merge_into.refresh_from_db()
        self.assertTrue(song_to_merge_into.artist_set.filter(pk=artist.pk).exists())

    def test_merges_artists_from_both_songs(self):
        # Arrange
        song_to_be_merged = self.create_song_to_be_merged()
        song_to_merge_into = song_factories.SongFactory()
        artist = artist_factories.ArtistFactory(songs=(song_to_be_merged,))
        artist_2 = artist_factories.ArtistFactory(songs=(song_to_merge_into,))

        # Act
        response = self.client.post(
            f"/admin/songs/song/{song_to_be_merged.id}/merge_song/",
            {"song_to_merge_into_id": song_to_merge_into.id, "commit": True},
            follow=True
        )

        # Assert
        self.assertRedirects(response, reverse(self.change_song_page, args=(song_to_merge_into.id,)))
        song_to_merge_into.refresh_from_db()
        self.assertTrue(song_to_merge_into.artist_set.filter(pk=artist.pk).exists())
        self.assertTrue(song_to_merge_into.artist_set.filter(pk=artist_2.pk).exists())

    def test_merge_does_not_duplicate_artists(self):
        # Arrange
        song_to_be_merged = self.create_song_to_be_merged()
        song_to_merge_into = song_factories.SongFactory()
        artist = artist_factories.ArtistFactory(songs=(song_to_be_merged, song_to_merge_into))

        # Act
        response = self.client.post(
            f"/admin/songs/song/{song_to_be_merged.id}/merge_song/",
            {"song_to_merge_into_id": song_to_merge_into.id, "commit": True},
            follow=True
        )

        # Assert
        self.assertRedirects(response, reverse(self.change_song_page, args=(song_to_merge_into.id,)))
        song_to_merge_into.refresh_from_db()
        self.assertEqual(song_to_merge_into.artist_set.count(), 1)
        self.assertTrue(song_to_merge_into.artist_set.filter(pk=artist.pk).exists())

    def test_merges_favorites(self):
        # Arrange
        song_to_be_merged = self.create_song_to_be_merged()
        song_to_merge_into = song_factories.SongFactory()
        profile_1 = factories.UserFactory().profile
        profile_2 = factories.UserFactory().profile
        profile_3 = factories.UserFactory().profile
        song_factories.FavoriteFactory(profile=profile_1, song=song_to_be_merged)
        song_factories.FavoriteFactory(profile=profile_2, song=song_to_merge_into)
        song_factories.FavoriteFactory(profile=profile_3, song=song_to_be_merged)
        song_factories.FavoriteFactory(profile=profile_3, song=song_to_merge_into)

        # Act
        response = self.client.post(
            f"/admin/songs/song/{song_to_be_merged.id}/merge_song/",
            {"song_to_merge_into_id": song_to_merge_into.id, "commit": True},
            follow=True
        )

        # Assert
        self.assertRedirects(response, reverse(self.change_song_page, args=(song_to_merge_into.id,)))
        self.assertEqual(song_to_merge_into.favorite_set.count(), 3)
        profiles_with_favorite = song_to_merge_into.favorite_set.all().values_list('profile', flat=True)
        self.assertIn(profile_1.id, profiles_with_favorite)
        self.assertIn(profile_2.id, profiles_with_favorite)
        self.assertIn(profile_3.id, profiles_with_favorite)

    def test_does_not_create_favorite_for_own_song(self):
        # Arrange
        song_to_be_merged = self.create_song_to_be_merged()
        song_to_merge_into = song_factories.SongFactory()
        profile = factories.UserFactory().profile
        artist_factories.ArtistFactory(user=profile.user, profile=profile, songs=(song_to_merge_into,))
        song_factories.FavoriteFactory(profile=profile, song=song_to_be_merged)

        # Act
        response = self.client.post(
            f"/admin/songs/song/{song_to_be_merged.id}/merge_song/",
            {"song_to_merge_into_id": song_to_merge_into.id, "commit": True},
            follow=True
        )

        # Assert
        self.assertRedirects(response, reverse(self.change_song_page, args=(song_to_merge_into.id,)))
        self.assertEqual(song_to_merge_into.favorite_set.count(), 0)

    def test_merges_comments(self):
        # Arrange
        song_to_be_merged = self.create_song_to_be_merged()
        song_to_merge_into = song_factories.SongFactory()
        profile_1 = factories.UserFactory().profile
        profile_2 = factories.UserFactory().profile
        comment = song_factories.CommentFactory(song=song_to_be_merged, profile=profile_1, rating=5, text="Hi")
        song_factories.CommentFactory(song=song_to_merge_into, profile=profile_2, rating=3, text="Hello")

        # Act
        response = self.client.post(
            f"/admin/songs/song/{song_to_be_merged.id}/merge_song/",
            {"song_to_merge_into_id": song_to_merge_into.id, "commit": True},
            follow=True
        )

        # Assert
        self.assertRedirects(response, reverse(self.change_song_page, args=(song_to_merge_into.id,)))
        self.assertEqual(song_to_merge_into.comment_set.count(), 2)
        song_to_merge_into.refresh_from_db()
        self.assertEqual(song_to_merge_into.songstats.average_comment_score, 4.0)
        self.assertEqual(song_to_merge_into.songstats.total_comments, 2)
        self.assertTrue(song_to_merge_into.comment_set.filter(text=comment.text, rating=comment.rating).exists())

    def test_does_not_merge_comments_for_own_song(self):
        # Arrange
        song_to_be_merged = self.create_song_to_be_merged()
        song_to_merge_into = song_factories.SongFactory()
        profile = factories.UserFactory().profile
        song_factories.CommentFactory(song=song_to_be_merged, profile=profile)
        artist_factories.ArtistFactory(user=profile.user, profile=profile, songs=(song_to_merge_into,))

        # Act
        response = self.client.post(
            f"/admin/songs/song/{song_to_be_merged.id}/merge_song/",
            {"song_to_merge_into_id": song_to_merge_into.id, "commit": True},
            follow=True
        )

        # Assert
        self.assertRedirects(response, reverse(self.change_song_page, args=(song_to_merge_into.id,)))
        self.assertEqual(song_to_merge_into.comment_set.count(), 0)

    def test_does_not_merge_comment_if_already_commented(self):
        # Arrange
        song_to_be_merged = self.create_song_to_be_merged()
        song_to_merge_into = song_factories.SongFactory()
        profile = factories.UserFactory().profile
        song_factories.CommentFactory(song=song_to_be_merged, profile=profile, rating=5, text="Hi")
        comment = song_factories.CommentFactory(song=song_to_merge_into, profile=profile, rating=3, text="Hello")

        # Act
        response = self.client.post(
            f"/admin/songs/song/{song_to_be_merged.id}/merge_song/",
            {"song_to_merge_into_id": song_to_merge_into.id, "commit": True},
            follow=True
        )

        # Assert
        self.assertRedirects(response, reverse(self.change_song_page, args=(song_to_merge_into.id,)))
        self.assertEqual(song_to_merge_into.comment_set.count(), 1)
        self.assertTrue(song_to_merge_into.comment_set.filter(text=comment.text, rating=comment.rating).exists())

    def test_make_featured_if_song_merged_from_was_featured(self):
        # Arrange
        featuring_profile = factories.UserFactory().profile
        song_to_be_merged = self.create_song_to_be_merged(featured_by=featuring_profile, featured_date=datetime.datetime(2020, 1, 1, tzinfo=datetime.timezone.utc))
        song_to_merge_into = song_factories.SongFactory()

        # Act
        self.client.post(
            f"/admin/songs/song/{song_to_be_merged.id}/merge_song/",
            {"song_to_merge_into_id": song_to_merge_into.id, "commit": True},
            follow=True
        )

        # Assert
        song_to_merge_into.refresh_from_db()
        self.assertTrue(song_to_merge_into.is_featured)
        self.assertEqual(song_to_merge_into.featured_by, featuring_profile)
        self.assertEqual(song_to_merge_into.featured_date, song_to_be_merged.featured_date)

    def test_select_nomination_info_from_first_song_if_featured_earlier(self):
        # Arrange
        featuring_profile = factories.UserFactory().profile
        second_featuring_profile = factories.UserFactory().profile
        song_to_be_merged = self.create_song_to_be_merged(featured_by=featuring_profile, featured_date=datetime.datetime(2020, 1, 1, tzinfo=datetime.timezone.utc))
        song_to_merge_into = song_factories.SongFactory(featured_by=second_featuring_profile, featured_date=datetime.datetime(2020, 1, 2, tzinfo=datetime.timezone.utc))

        # Act
        self.client.post(
            f"/admin/songs/song/{song_to_be_merged.id}/merge_song/",
            {"song_to_merge_into_id": song_to_merge_into.id, "commit": True},
            follow=True
        )

        # Assert
        song_to_merge_into.refresh_from_db()
        self.assertTrue(song_to_merge_into.is_featured)
        self.assertEqual(song_to_merge_into.featured_by, featuring_profile)
        self.assertEqual(song_to_merge_into.featured_date, song_to_be_merged.featured_date)

    def test_select_nomination_info_from_second_song_if_featured_earlier(self):
        # Arrange
        featuring_profile = factories.UserFactory().profile
        second_featuring_profile = factories.UserFactory().profile
        song_to_be_merged = self.create_song_to_be_merged(featured_by=featuring_profile, featured_date=datetime.datetime(2020, 1, 2, tzinfo=datetime.timezone.utc))
        song_to_merge_into = song_factories.SongFactory(is_featured=True, featured_by=second_featuring_profile, featured_date=datetime.datetime(2020, 1, 1, tzinfo=datetime.timezone.utc))

        # Act
        self.client.post(
            f"/admin/songs/song/{song_to_be_merged.id}/merge_song/",
            {"song_to_merge_into_id": song_to_merge_into.id, "commit": True},
            follow=True
        )

        # Assert
        song_to_merge_into.refresh_from_db()
        self.assertTrue(song_to_merge_into.is_featured)
        self.assertEqual(song_to_merge_into.featured_by, second_featuring_profile)
        self.assertEqual(song_to_merge_into.featured_date, song_to_merge_into.featured_date)
