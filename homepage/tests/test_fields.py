from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from homepage.fields import BlacklistProtectedEmailField
from homepage.models import BlacklistedDomain

class UniqueEmailFieldTests(TestCase):
    illegal_email_address = 'testuser@wobsite.com'
    
    def setUp(self):
        user = User.objects.create(username='test_user', email='testuser@test.com')
        BlacklistedDomain.objects.create(domain='wobsite.com', added_by=user)

    def test_clean_does_not_allow_email_address_from_blacklisted_domain(self):
        # Arrange
        field = BlacklistProtectedEmailField()
        
        # Act
        with self.assertRaisesMessage(ValidationError, BlacklistProtectedEmailField.blacklisted_email_error_message):
            field.clean(self.illegal_email_address)