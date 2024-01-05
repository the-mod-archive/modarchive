from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls.base import reverse

from homepage.tests import factories

class UploadViewTests(TestCase):
    def test_screening_view_permits_access_to_authenticated_users(self):
        user = factories.UserFactory()
        permission = Permission.objects.get(codename='can_approve_songs')
        user.user_permissions.add(permission)
        self.client.force_login(user)

        response = self.client.get(reverse('screen_songs'))

        # Assert
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, "screening.html")

    def test_screening_view_rejects_access_to_unauthenticated_users(self):
        response = self.client.get(reverse('screen_songs'))
        screening_url = reverse('screen_songs')
        login_url = reverse('login')

        # Assert
        self.assertEqual(302, response.status_code)
        self.assertRedirects(response, f"{login_url}?next={screening_url}")

    def test_screening_view_rejects_access_to_users_with_insufficient_permissions(self):
        user = factories.UserFactory()
        self.client.force_login(user)

        response = self.client.get(reverse('screen_songs'))

        # Assert
        self.assertEqual(403, response.status_code)
