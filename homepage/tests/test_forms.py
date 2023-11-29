from django.test import TestCase
from homepage import forms
from homepage.tests import factories
from django.contrib.auth.models import User

FIELD_REQUIRED_ERROR_MESSAGE = 'This field is required.'

class ForgotPasswordFormTests(TestCase):
    def test_form_without_email_address_is_invalid(self):
        # Arrange
        form = forms.ForgotPasswordForm(data={})

        # Act
        is_valid = form.is_valid()

        # Assert
        self.assertFalse(is_valid, 'Form should not have been valid with missing email address')
        self.assertEqual([FIELD_REQUIRED_ERROR_MESSAGE], form.errors['email'], 'Error message for missing email address was incorrect.')

    def test_form_with_malformed_email_address_is_invalid(self):
        # Arrange
        form = forms.ForgotPasswordForm(data={'email': 'asdfv@@asdf'})

        # Act
        is_valid = form.is_valid()

        # Assert
        self.assertFalse(is_valid, 'Form should not have been valid with malformed email address')
        self.assertEqual(['Enter a valid email address.'], form.errors['email'], 'Error message for malformed email address was incorrect.')

    def test_form_with_valid_email_address_is_valid(self):
        # Arrange
        form = forms.ForgotPasswordForm(data={'email': 'testuser@test.com'})

        # Act
        is_valid = form.is_valid()

        # Assert
        self.assertTrue(is_valid, 'Form should have been valid with valid email address.')

class ResetPasswordFormTests(TestCase):
    strong_password = "abc123!iz1"
    weak_password = "password"


    def setUp(self):
        self.user = factories.UserFactory(password='testpassword') 

    def test_form_with_strong_matching_passwords_is_valid(self):
        # Arrange
        form = forms.ResetPasswordForm(data={'new_password1': self.strong_password, 'new_password2': self.strong_password}, user=self.user)

        # Assert
        self.assertTrue(form.is_valid, 'Form with strong matching passwords should have been valid.')
        self.assertEqual(0, len(form.errors), f'Expected no errors but got { len(form.errors) }')

    def test_form_with_weak_matching_passwords_is_invalid(self):
        # Arrange
        form = forms.ResetPasswordForm(data={'new_password1': self.weak_password, 'new_password2': self.weak_password}, user=self.user)

        # Assert
        self.assertFalse(form.is_valid(), 'Form with weak matching passwords should not have been valid.')
        self.assertEqual(1, len(form.errors), f'Expected 1 error but got {len(form.errors)}')
        self.assertEqual(['This password is too common.'], form.errors['new_password2'], 'Error message for weak password was incorrect.')

    def test_form_missing_first_password_is_invalid(self):
        # Arrange
        form = forms.ResetPasswordForm(data={'new_password2': self.strong_password}, user=self.user)

        # Assert
        self.assertFalse(form.is_valid(), 'Form with missing first password should not have been valid.')
        self.assertEqual(1, len(form.errors), f'Expected 1 error but got {len(form.errors)}')
        self.assertEqual([FIELD_REQUIRED_ERROR_MESSAGE], form.errors['new_password1'])

    def test_form_missing_second_password_is_invalid(self):
        # Arrange
        form = forms.ResetPasswordForm(data={'new_password1': self.strong_password}, user=self.user)

        # Assert
        self.assertFalse(form.is_valid(), 'Form with missing second password should not have been valid.')
        self.assertEqual(1, len(form.errors), f'Expected 1 error but got {len(form.errors)}')
        self.assertEqual([FIELD_REQUIRED_ERROR_MESSAGE], form.errors['new_password2'])

    def test_form_missing_both_passwords_is_invalid(self):
        # Arrange
        form = forms.ResetPasswordForm(data={}, user=self.user)

        # Assert
        self.assertFalse(form.is_valid(), 'Form with both passwords missing should not have been valid.')
        self.assertEqual(2, len(form.errors), f'Expected 2 errors but got {len(form.errors)}')
        self.assertEqual([FIELD_REQUIRED_ERROR_MESSAGE], form.errors['new_password1'])
        self.assertEqual([FIELD_REQUIRED_ERROR_MESSAGE], form.errors['new_password2'])

    def test_form_with_mismatching_passwords_is_invalid(self):
        # Arrange 
        form = forms.ResetPasswordForm(data={'new_password1': self.strong_password, 'new_password2': f'{self.strong_password}azdazd'}, user=self.user)

        # Assert
        self.assertFalse(form.is_valid(), 'Form with mismatching password should not have been valid.')
        self.assertEqual(1, len(form.errors), f'Expected 1 error but got {len(form.errors)}')
        self.assertEqual(["The two password fields didn’t match."], form.errors['new_password2'], 'Error message for mismatching passwords was incorrect.')

class RegisterUserFormTests(TestCase):
    strong_password = "abc123!iz1"
    weak_password = "password"
    email_address = 'test@test.com'
    duplicate_email_address = 'testuser@website.com'
    existing_username = 'test_user'
    new_username = 'new_user'
    additional_username = 'additional_user'

    def get_form_data(self, username = new_username, email = email_address, password1 = strong_password, password2 = strong_password):
        return {
            'username': username,
            'email': email,
            'password1': password1,
            'password2': password2
        }

    def setUp(self):
        self.user = factories.UserFactory(username=self.existing_username, email=self.duplicate_email_address, password='testpassword')

    def test_raises_error_if_email_address_already_in_use(self):
        # Arrange
        form = forms.RegisterUserForm(data = self.get_form_data(email = self.duplicate_email_address))

        # Assert
        self.assertTrue(form.is_valid(), "Form with duplicate email address should be valid, in spite of what you may think.")
        with self.assertRaisesMessage(forms.EmailAddressInUseError, "Email address is already in use."):
            form.save()

    def test_creates_inactive_user(self):
        # Arrange
        form = forms.RegisterUserForm(data = self.get_form_data(username=self.additional_username))

        # Act
        form.save()
        user = User.objects.get(email = self.email_address)

        # Assert
        self.assertEqual(self.additional_username, user.username, "Username did not match")
        self.assertFalse(user.is_active, "New user should not be active before account activation")

    def test_completed_form_is_valid(self):
        # Arrange
        form = forms.RegisterUserForm(data=self.get_form_data())
        
        # Assert
        self.assertTrue(form.is_valid(), "Expected completed form to be valid.")
    
    def test_form_with_duplicate_username_is_invalid(self):
        # Arrange
        form = forms.RegisterUserForm(data=self.get_form_data(username=self.existing_username))
        
        # Assert
        self.assertFalse(form.is_valid(), "Form with already existing username should not be valid.")
        self.assertEqual(1, len(form.errors), f"Expected 1 error but got {len(form.errors)}")
        self.assertEqual(["A user with that username already exists."], form.errors['username'], "Error message for duplicate username is incorrect.")

    def test_form_with_weak_password_is_invalid(self):
        # Arrange
        form = forms.RegisterUserForm(data=self.get_form_data(password1=self.weak_password, password2=self.weak_password))
        
        # Assert
        self.assertFalse(form.is_valid(), "Form with weak password should not be valid.")
        self.assertEqual(1, len(form.errors), f"Expected 1 error but got {len(form.errors)}")
        self.assertEqual(["This password is too common."], form.errors['password2'], "Error message for weak password is incorrect.")

    def test_form_missing_username_is_invalid(self):
        # Arrange
        form = forms.RegisterUserForm(data=self.get_form_data(username=None))
        
        # Assert
        self.assertFalse(form.is_valid(), "Form without username should not be valid.")
        self.assertEqual(1, len(form.errors), f"Expected 1 error but got {len(form.errors)}")
        self.assertEqual([FIELD_REQUIRED_ERROR_MESSAGE], form.errors['username'], "Error message for missing username is incorrect.")

    def test_form_missing_email_address_is_invalid(self):
        # Arrange
        form = forms.RegisterUserForm(data=self.get_form_data(email=None))
        
        # Assert
        self.assertFalse(form.is_valid(), "Form without email should not be valid.")
        self.assertEqual(1, len(form.errors), f"Expected 1 error but got {len(form.errors)}")
        self.assertEqual([FIELD_REQUIRED_ERROR_MESSAGE], form.errors['email'], "Error message for missing email is incorrect.")

    def test_form_missing_password_is_invalid(self):
        # Arrange
        form = forms.RegisterUserForm(data=self.get_form_data(password2=None, password1=None))
        
        # Assert
        self.assertFalse(form.is_valid(), "Form without password should not be valid.")
        self.assertEqual(2, len(form.errors), f"Expected 2 errors but got {len(form.errors)}")
        self.assertEqual([FIELD_REQUIRED_ERROR_MESSAGE], form.errors['password1'], "Error message for missing password is incorrect.")
        self.assertEqual([FIELD_REQUIRED_ERROR_MESSAGE], form.errors['password2'], "Error message for missing password is incorrect.")

    def test_form_with_mismatching_passwords_is_invalid(self):
        # Arrange
        form = forms.RegisterUserForm(data=self.get_form_data(password1=f"1234{self.strong_password}"))
        
        # Assert
        self.assertFalse(form.is_valid(), "Form with mismatching passwords should not be valid.")
        self.assertEqual(1, len(form.errors), f"Expected 1 error but got {len(form.errors)}")
        self.assertEqual(["The two password fields didn’t match."], form.errors['password2'], "Error message for mismatching passwords is incorrect.")

class UpdateProfileFormTests(TestCase):
    def test_form_with_empty_blurb_is_valid(self):
        form = forms.UpdateProfileForm(data={'blurb': ''})
        self.assertTrue(form.is_valid())

    def test_form_with_no_blurb_is_valid(self):
        form = forms.UpdateProfileForm(data={})
        self.assertTrue(form.is_valid())

    def test_form_with_excessive_blurb_is_invalid(self):
        extra_long_blurb = "long blurb" * 2401
        form = forms.UpdateProfileForm(data={'blurb': extra_long_blurb})

        self.assertFalse(form.is_valid())