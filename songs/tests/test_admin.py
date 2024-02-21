from django.test import TestCase

from homepage.tests import factories
from songs import factories as song_factories

class MergeSongTests(TestCase):
    def setUp(self):
        self.user = factories.UserFactory(is_staff=True)
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
