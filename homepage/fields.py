from django.forms.fields import EmailField
from django.core.exceptions import ValidationError
from homepage.models import BlacklistedDomain

class BlacklistProtectedEmailField(EmailField):
    blacklisted_email_error_message = 'We do not currently accept account registrations using this email domain. Please use an email address from a different domain.'

    def clean(self, value):
        # Run the parent method first to verify that email address is in a valid format
        cleaned_value = super().clean(value)

        # Verify that email is not from a banned domain
        domain = cleaned_value.split('@')[1]
        blacklisted_domains = BlacklistedDomain.objects.filter(domain=domain)
        if blacklisted_domains:
            blacklisted_domains[0].hits = blacklisted_domains[0].hits + 1
            blacklisted_domains[0].save()
            raise ValidationError(self.blacklisted_email_error_message)
         
        return cleaned_value