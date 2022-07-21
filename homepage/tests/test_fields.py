from django.core.exceptions import ValidationError
from django.test import TestCase
from homepage.fields import BlacklistProtectedEmailField
from homepage.tests import factories

class UniqueEmailFieldTests(TestCase):
    def test_clean_does_not_allow_email_address_from_blacklisted_domain(self):
        # Arrange
        factories.BlacklistedDomainFactory(domain='wobsite.com', added_by=factories.UserFactory())
        
        # Act
        with self.assertRaisesMessage(ValidationError, BlacklistProtectedEmailField.blacklisted_email_error_message):
            BlacklistProtectedEmailField().clean('testuser@wobsite.com')