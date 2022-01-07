from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase
from django.urls.base import reverse

class ForgotPasswordViewTests(TestCase):
    def setUp(self):
        User.objects.create_user(username='test_user', email='testuser@test.com', password='testpassword')

    def test_get_request_redirects_authenticated_user(self):
        # Arrange
        self.client.login(username='test_user', password='testpassword')

        # Act
        response = self.client.get(reverse('forgot_password'))

        # Assert
        self.assertRedirects(response, reverse('home'))

    def test_get_request_returns_ok_when_not_authenticated(self):
        # Act
        response = self.client.get(reverse('forgot_password'))

        # Assert
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed('templates/forgot_password.html')

    def test_post_request_redirects_authenticated_user(self):
        # Arrange
        self.client.login(username='test_user', password='testpassword')

        # Act
        response = self.client.post(reverse('forgot_password'), {'email': 'testuser@test.com'})

        # Assert
        self.assertRedirects(response, reverse('home'))

    def test_post_request_redirects_to_password_reset_done_when_not_authenticated(self):
        # Act
        response = self.client.post(reverse('forgot_password'), {'email': 'testuser@test.com'})

        # Assert
        self.assertRedirects(response, reverse('password_reset_done'))
        self.assertTemplateUsed('templates/password_reset_done.html')

    def test_successful_post_sends_email(self):
        # Act
        self.client.post(reverse('forgot_password'), {'email': 'testuser@test.com'})

        # Assert
        self.assertEqual(1, len(mail.outbox))
        self.assertEqual(['testuser@test.com'], mail.outbox[0].to)
        self.assertEqual('donotreply@modarchive.org', mail.outbox[0].from_email)
        self.assertEqual('Your ModArchive password has been reset', mail.outbox[0].subject)
        self.assertTrue('You have requested a password reset for your ModArchive account. To reset your password, please follow the link below.' in mail.outbox[0].body)

    def test_successful_post_with_email_not_in_database_does_not_send_email(self):
        # Act
        self.client.post(reverse('forgot_password'), {'email': 'notindatabase@test.com'})
        
        # Assert
        self.assertEqual(0, len(mail.outbox))

class CustomPasswordResetConfirmViewTests(TestCase):
    kwargs = {'uidb64': 'Mg', 'token': 'asdfasdf'}

    def setUp(self):
        User.objects.create_user(username='test_user', email='testuser@test.com', password='testpassword')

    def test_get_request_redirects_authenticated_user(self):
        # Arrange
        self.client.login(username='test_user', password='testpassword')

        # Act
        response = self.client.get(reverse('password_reset', kwargs=self.kwargs))

        # Assert
        self.assertRedirects(response, reverse('home'))

    def test_post_request_redirects_authenticated_user(self):
        # Arrange
        self.client.login(username='test_user', password='testpassword')

        # Act
        response = self.client.post(reverse('password_reset', kwargs=self.kwargs))

        # Assert
        self.assertRedirects(response, reverse('home'))

class CustomPasswordResetCompleteViewTests(TestCase):
    def setUp(self):
        User.objects.create_user(username='test_user', email='testuser@test.com', password='testpassword')

    def test_get_request_redirects_authenticated_user(self):
        # Arrange
        self.client.login(username='test_user', password='testpassword')

        # Act
        response = self.client.get(reverse('password_reset_complete'))

        # Assert
        self.assertRedirects(response, reverse('home'))

    def test_post_request_redirects_authenticated_user(self):
        # Arrange
        self.client.login(username='test_user', password='testpassword')

        # Act
        response = self.client.post(reverse('password_reset_complete'))

        # Assert
        self.assertRedirects(response, reverse('home'))