from django.test import TestCase
from django.urls import reverse

from songs import factories as song_factories
from uploads import factories as upload_factories
from homepage.tests import factories

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
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, "pending_uploads.html")

    def test_only_retrieves_pending_uploads_for_authenticated_user(self):
        # Arrange
        user = factories.UserFactory()
        user_2 = factories.UserFactory()
        self.client.force_login(user)

        song_1 = upload_factories.NewSongFactory(filename='song1.mod', uploader_profile=user.profile)
        song_2 = upload_factories.NewSongFactory(filename='song2.mod', uploader_profile=user.profile)
        song_3 = upload_factories.NewSongFactory(filename='song3.mod', uploader_profile=user_2.profile)

        # Act
        response = self.client.get(reverse('pending_uploads'))

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pending_uploads.html')
        self.assertQuerySetEqual(
            response.context['pending_uploads'],
            [song_1, song_2],
            ordered=False
        )
        self.assertNotIn(repr(song_3), response.content.decode())
