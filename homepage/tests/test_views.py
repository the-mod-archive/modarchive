from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase
from django.urls.base import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from unittest.mock import patch

from artists.models import Artist
from homepage.models import Profile
from homepage.tokens import account_activation_token
from songs.models import Comment, Song

class PasswordResetViewTests(TestCase):
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
        self.assertTemplateUsed('templates/password_reset/forgot_password.html')

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
        self.assertTemplateUsed('templates/password_reset/password_reset_done.html')

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

class PasswordResetConfirmViewTests(TestCase):
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

class PasswordResetCompleteViewTests(TestCase):
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

class RegistrationTests(TestCase):
    def test_redirects_authenticated_user(self):
        # Arrange
        User.objects.create_user(username='test_user', email='testuser@test.com', password='testpassword')
        self.client.login(username='test_user', password='testpassword')

        # Act
        response = self.client.get(reverse('register'))

        # Assert
        self.assertRedirects(response, reverse('home'))
    
    def test_renders_registration_form(self):
        # Act
        response = self.client.get(reverse('register'))

        # Assert
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed('templates/registration/register.html')

    def test_renders_registration_form_if_submit_is_invalid(self):
        # Act
        response = self.client.post(reverse('register'), {})
        
        # Assert
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed('templates/registration/register.html')

    @patch("homepage.view.registration_views.is_recaptcha_success")
    def test_sends_registration_email_with_completed_form(self, mock_recaptcha):
        # Act
        mock_recaptcha.return_value = True
        response = self.client.post(reverse('register'), {'username': 'new_user', 'email': 'newuser@test.com', 'password1': 'abcdef123!', 'password2': 'abcdef123!'})

        # Assert 
        self.assertRedirects(response, reverse('register_done'))
        self.assertEqual(1, len(mail.outbox))
        self.assertEqual(['newuser@test.com'], mail.outbox[0].to)
        self.assertEqual('donotreply@modarchive.org', mail.outbox[0].from_email)
        self.assertEqual("Active your ModArchive account", mail.outbox[0].subject)
        self.assertTrue("Thank you for registering an account with the Mod Archive. To complete your registration, please follow this link:" in mail.outbox[0].body)
        self.assertTrue("https://testserver/activate_account" in mail.outbox[0].body)

    @patch("homepage.view.registration_views.is_recaptcha_success")
    def test_notifies_existing_user_if_email_address_already_in_use(self, mock_recaptcha):
        # Arrange
        mock_recaptcha.return_value = True
        User.objects.create_user(username='test_user', email='testuser@test.com', password='testpassword')

        # Act
        response = self.client.post(reverse('register'), {'username': 'new_user', 'email': 'testuser@test.com', 'password1': 'abcdef123!', 'password2': 'abcdef123!'})

        # Assert
        self.assertRedirects(response, reverse('register_done'))
        self.assertEqual(1, len(mail.outbox))
        self.assertEqual(['testuser@test.com'], mail.outbox[0].to)
        self.assertEqual('donotreply@modarchive.org', mail.outbox[0].from_email)
        self.assertEqual("ModArchive security warning", mail.outbox[0].subject)
        self.assertTrue("A user attempted to register a ModArchive account with your email address." in mail.outbox[0].body)

    @patch("homepage.view.registration_views.is_recaptcha_success")
    def test_redirects_to_register_fail_if_recaptcha_fails(self, mock_recaptcha):
        # Arrange
        mock_recaptcha.return_value = False
        
        # Act
        response = self.client.post(reverse('register'), {'username': 'new_user', 'email': 'newuser@test.com', 'password1': 'abcdef123!', 'password2': 'abcdef123!'})

        # Assert 
        self.assertRedirects(response, reverse('register_fail'))

    @patch("homepage.view.registration_views.is_recaptcha_success")
    def test_registration_creates_user_but_not_profile(self, mock_recaptcha):
        # Act
        mock_recaptcha.return_value = True
        self.client.post(reverse('register'), {'username': 'new_user', 'email': 'newuser@test.com', 'password1': 'abcdef123!', 'password2': 'abcdef123!'})

        # Assert
        user = User.objects.get(username = 'new_user')
        self.assertIsNotNone(user)
        self.assertFalse(hasattr(user, 'profile'))

class ActivationTests(TestCase):
    kwargs = {'uidb64': 'Mg', 'token': 'asdfasdf'}

    def test_redirects_authenticated_user(self):
        # Arrange
        User.objects.create_user(username='test_user', email='testuser@test.com', password='testpassword')
        self.client.login(username='test_user', password='testpassword')

        # Act
        response = self.client.get(reverse('activate_account', kwargs=self.kwargs))

        # Assert
        self.assertRedirects(response, reverse('home'))

    def test_activates_user(self):
        # Arrange
        user = User.objects.create_user(username='test_user', email='testuser@test.com', password='testpassword', is_active=False)
        token = account_activation_token.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        # Act
        response = self.client.get(reverse('activate_account', kwargs={'uidb64': uid, 'token': token}))

        # Assert
        self.assertRedirects(response, reverse('account_activation_complete'))
        user.refresh_from_db()
        self.assertTrue(user.is_active, "Expected user to be active")

    def test_creates_profile_on_user_activation(self):
        # Arrange
        user = User.objects.create_user(username='test_user', email='testuser@test.com', password='testpassword', is_active=False)
        token = account_activation_token.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        # Act
        self.client.get(reverse('activate_account', kwargs={'uidb64': uid, 'token': token}))

        # Assert
        user.refresh_from_db()
        self.assertTrue(hasattr(user, 'profile'))
        profile = user.profile
        self.assertIsNotNone(profile, "Expected profile to exist for user")
        self.assertEqual(user.username, profile.display_name, "Profile display name did not match username")

    def test_redirects_to_home_if_user_already_active(self):
        # Arrange
        user = User.objects.create_user(username='test_user', email='testuser@test.com', password='testpassword', is_active=True)
        token = account_activation_token.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        # Act
        response = self.client.get(reverse('activate_account', kwargs={'uidb64': uid, 'token': token}))

        # Assert
        self.assertRedirects(response, reverse('home'))

    def test_redirects_to_error_page_if_something_goes_wrong(self):
        # Arrange
        user = User.objects.create_user(username='test_user', email='testuser@test.com', password='testpassword', is_active=True)
        token = account_activation_token.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        user.delete()

        # Act
        response = self.client.get(reverse('activate_account', kwargs={'uidb64': uid, 'token': token}))

        # Assert
        self.assertRedirects(response, reverse('activation_error'))

class LegacyRedirectionViewTests(TestCase):
    fixtures = ["songs.json"]

    def test_redirects_to_home_if_no_match_found(self):
        response = self.client.get('/login.php/?blarg=blag')
        self.assertRedirects(response, reverse('home'))
    
    def test_mixed_case_query_param_still_redirects(self):
        response = self.client.get('/login.php/?request=lOg_iN')
        self.assertRedirects(response, reverse('login'))

    def test_old_login_url_redirects(self):
        response = self.client.get('/login.php/?request=log_in')
        self.assertRedirects(response, reverse('login'))

    def test_old_forgot_password_url_redirects(self):
        response = self.client.get('/assistance.php/?request=forgot_password_page')
        self.assertRedirects(response, reverse('forgot_password'))

    def test_old_change_password_url_redirects(self):
        User.objects.create_user(username='test_user', email='testuser@test.com', password='testpassword')
        self.client.login(username='test_user', password='testpassword')
        response = self.client.get('/interactive.php/?request=change_password_page')
        self.assertRedirects(response, reverse('change_password'))

    def test_old_register_url_redirects(self):
        response = self.client.get('/assistance.php/?request=create_account_page')
        self.assertRedirects(response, reverse('register'))

    def test_old_module_url_redirects(self):
        response = self.client.get('/index.php/?request=view_by_moduleid&query=48552')
        self.assertRedirects(response, reverse('view_song', kwargs = {'pk': 1}))

    def test_old_module_url_redirects_to_home_for_invalid_id(self):
        response = self.client.get('/index.php/?request=view_by_moduleid&query=99999')
        self.assertRedirects(response, reverse('home'))

class ProfileViewTests(TestCase):
    def test_profile_page_contains_requested_profile(self):
        # Arrange
        user = User.objects.create_user(username='test_user', email='testuser@test.com', password='testpassword', is_active=True)
        profile = Profile.objects.create(id = 1, user = user, display_name = 'Arcturus')
        
        # Act
        response = self.client.get(reverse('view_profile', kwargs = {'pk': 1}))

        # Assert
        self.assertTemplateUsed(response, 'profile.html')
        self.assertTrue('profile' in response.context)

        profile = response.context['profile']
        self.assertEquals('Arcturus', profile.display_name)

    def test_profile_page_responds_with_404_when_profile_does_not_exist(self):
        # Act
        response = self.client.get(reverse('view_profile', kwargs = {'pk': 42}))

        # Assert
        self.assertEqual(response.status_code, 404)

    def test_redirect_to_artist_page_if_exists_for_profile(self):
        # Arrange
        user = User.objects.create_user(username='test_user', email='testuser@test.com', password='testpassword', is_active=True)
        profile = Profile.objects.create(id = 1, user = user, display_name = 'Arcturus')
        Artist.objects.create(id = 2, profile = profile, name = 'Arcturus')

        # Act
        response = self.client.get(reverse('view_profile', kwargs = {'pk': 1}))

        # Assert
        self.assertRedirects(response, reverse('view_artist', kwargs = {'pk': 2}))

class UpdateProfileViewTests(TestCase):
    fixtures = ["users.json"]

    def test_get_update_profile_redirects_unauthenticated_user(self):
        # Arrange
        update_profile_url = reverse('update_profile')
        
        # Act
        response = self.client.get(reverse('update_profile'))

        # Assert
        self.assertRedirects(response, f'/login/?next={update_profile_url}')

    def test_get_update_profile_handles_error_when_user_has_no_profile(self):
        # Arrange
        self.client.force_login(User.objects.get_or_create(username='test_no_profile')[0])

        # Act
        response = self.client.get(reverse('update_profile'))

        # Assert
        self.assertEqual(404, response.status_code)

    def test_get_update_profile_includes_correct_profile(self):
        # Arrange
        self.client.force_login(User.objects.get_or_create(username='test_user')[0])
        profile = Profile.objects.get(id = 1)

        # Act
        response = self.client.get(reverse('update_profile'))

        # Assert
        self.assertTemplateUsed(response, 'update_profile.html')
        self.assertTrue('profile' in response.context)
        self.assertEquals(profile.display_name, response.context['profile'].display_name)

    def test_post_update_profile_redirects_unauthenticated_user(self):  
        # Arrange
        update_profile_url = reverse('update_profile')
        
        # Act
        response = self.client.post(reverse('update_profile'))

        # Assert
        self.assertRedirects(response, f'/login/?next={update_profile_url}')

    def test_post_update_profile_handles_error_when_user_has_no_profile(self):
        # Arrange
        self.client.force_login(User.objects.get_or_create(username='test_no_profile')[0])

        # Act
        response = self.client.post(reverse('update_profile'), {'blurb': 'new blurb'})

        # Assert
        self.assertEqual(404, response.status_code)

    def test_post_update_profile_successfully_updates_profile(self):
        # Arrange
        self.client.force_login(User.objects.get_or_create(username='test_user')[0])
        profile = Profile.objects.get(id = 1)

        # Act
        self.client.post(reverse('update_profile'), {'blurb': 'new blurb'})

        # Assert
        profile.refresh_from_db()
        self.assertEqual('new blurb', profile.blurb)