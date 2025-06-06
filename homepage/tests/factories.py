import factory

from django.contrib.auth import models as auth_models

from homepage import models

class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = auth_models.User

    username = factory.Sequence(lambda n: 'test_user_%d' % n)
    email = factory.LazyAttribute(lambda o: '%s@example.org' % o.username)

class BlacklistedDomainFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.BlacklistedDomain

class NewsFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.News

    headline = factory.Sequence(lambda n: 'Headline %d' % n)
    content = factory.Sequence(lambda n: 'This is news content')
