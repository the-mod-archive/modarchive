import factory

from django.contrib.auth.models import User

from homepage.models import BlacklistedDomain

class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: 'test_user_%d' % n)
    email = factory.LazyAttribute(lambda o: '%s@example.org' % o.username)

class BlacklistedDomainFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = BlacklistedDomain