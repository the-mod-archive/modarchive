from django.test import TestCase
from homepage.forms import ForgotPasswordForm, ResetPasswordForm
from django.contrib.auth.models import User

class ForgotPasswordFormTests(TestCase):
    def test_form_without_email_address_is_invalid(self):
        # Arrange
        form = ForgotPasswordForm(data={})

        # Act
        is_valid = form.is_valid()

        # Assert
        self.assertFalse(is_valid, 'Form should not have been valid with missing email address')
        self.assertEquals(['This field is required.'], form.errors['email'], 'Error message for missing email address was incorrect.')

    def test_form_with_malformed_email_address_is_invalid(self):
        # Arrange
        form = ForgotPasswordForm(data={'email': 'asdfv@@asdf'})

        # Act
        is_valid = form.is_valid()

        # Assert
        self.assertFalse(is_valid, 'Form should not have been valid with malformed email address')
        self.assertEquals(['Enter a valid email address.'], form.errors['email'], 'Error message for malformed email address was incorrect.')

    def test_form_with_valid_email_address_is_valid(self):
        # Arrange
        form = ForgotPasswordForm(data={'email': 'testuser@test.com'})

        # Act
        is_valid = form.is_valid()

        # Assert
        self.assertTrue(is_valid, 'Form should have been valid with valid email address.')

class ResetPasswordFormTests(TestCase):
    strong_password = "abc123!iz1"
    weak_password = "password"

    def setUp(self) -> None:
        self.user = User.objects.create_user(username='test_user', email='testuser@test.com', password='testpassword')

    def test_form_with_strong_matching_passwords_is_valid(self):
        # Arrange
        form = ResetPasswordForm(data={'new_password1': self.strong_password, 'new_password2': self.strong_password}, user=self.user)

        # Assert
        self.assertTrue(form.is_valid, 'Form with strong matching passwords should have been valid.')
        self.assertEquals(0, len(form.errors), f'Expected no errors but got { len(form.errors) }')

    def test_form_with_weak_matching_passwords_is_invalid(self):
        # Arrange
        form = ResetPasswordForm(data={'new_password1': self.weak_password, 'new_password2': self.weak_password}, user=self.user)

        # Assert
        self.assertFalse(form.is_valid(), 'Form with weak matching passwords should not have been valid.')
        self.assertEquals(1, len(form.errors), f'Expected 1 error but got {len(form.errors)}')
        self.assertEquals(['This password is too common.'], form.errors['new_password2'], 'Error message for weak password was incorrect.')

    def test_form_missing_first_password_is_invalid(self):
        # Arrange
        form = ResetPasswordForm(data={'new_password2': self.strong_password}, user=self.user)

        # Assert
        self.assertFalse(form.is_valid(), 'Form with missing first password should not have been valid.')
        self.assertEquals(1, len(form.errors), f'Expected 1 error but got {len(form.errors)}')
        self.assertEquals(['This field is required.'], form.errors['new_password1'], 'Error message for missing password field was incorrect.')

    def test_form_missing_second_password_is_invalid(self):
        # Arrange
        form = ResetPasswordForm(data={'new_password1': self.strong_password}, user=self.user)

        # Assert
        self.assertFalse(form.is_valid(), 'Form with missing second password should not have been valid.')
        self.assertEquals(1, len(form.errors), f'Expected 1 error but got {len(form.errors)}')
        self.assertEquals(['This field is required.'], form.errors['new_password2'], 'Error message for missing password field was incorrect.')

    def test_form_missing_both_passwords_is_invalid(self):
        # Arrange
        form = ResetPasswordForm(data={}, user=self.user)

        # Assert
        self.assertFalse(form.is_valid(), 'Form with both passwords missing should not have been valid.')
        self.assertEquals(2, len(form.errors), f'Expected 2 errors but got {len(form.errors)}')
        self.assertEquals(["This field is required."], form.errors['new_password1'], 'Error message for missing password field was incorrect.')
        self.assertEquals(["This field is required."], form.errors['new_password2'], 'Error message for missing password field was incorrect.')

    def test_form_with_mismatching_passwords_is_invalid(self):
        # Arrange 
        form = ResetPasswordForm(data={'new_password1': self.strong_password, 'new_password2': f'{self.strong_password}azdazd'}, user=self.user)

        # Assert
        self.assertFalse(form.is_valid(), 'Form with mismatching password should not have been valid.')
        self.assertEquals(1, len(form.errors), f'Expected 1 error but got {len(form.errors)}')
        self.assertEquals(["The two password fields didn’t match."], form.errors['new_password2'], 'Error message for mismatching passwords was incorrect.')