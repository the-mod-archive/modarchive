from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from homepage.fields import UniqueEmailField
from homepage.models import BlacklistedDomain

class UniqueEmailFieldTests(TestCase):
    duplicate_email_address = 'testuser@test.com'
    illegal_email_address = 'testuser@wobsite.com'
    
    def setUp(self):
        user = User.objects.create(username='test_user', email=self.duplicate_email_address)
        BlacklistedDomain.objects.create(domain='wobsite.com', added_by=user)

    def test_clean_does_not_allow_duplicate_email_addresses(self):
        # Arrange
        field = UniqueEmailField()

        # Act
        with self.assertRaisesMessage(ValidationError, UniqueEmailField.duplicate_email_error_message):
            field.clean(self.duplicate_email_address)

    def test_clean_does_not_allow_email_address_from_blacklisted_domain(self):
        # Arrange
        field = UniqueEmailField()
        
        # Act
        with self.assertRaisesMessage(ValidationError, UniqueEmailField.blacklisted_email_error_message):
            field.clean(self.illegal_email_address)

