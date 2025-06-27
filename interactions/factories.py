import factory

from interactions import models
from songs.factories import SongFactory

class CommentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Comment

    song = factory.SubFactory(SongFactory)
    rating = 5

class FavoriteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Favorite

class ArtistCommentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.ArtistComment
