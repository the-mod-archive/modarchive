import factory

from songs import models

class SongFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Song

    format = models.Song.Formats.S3M
    filename = factory.Sequence(lambda n: 'song_%d.s3m' % n)
    title = factory.Sequence(lambda n: 'Song %d' % n)
    file_size = 200000
    channels = 16
    hash = "abcdef1234567890"
    pattern_hash = "abcdef1234567890"
    instrument_text = "instrument text"
    comment_text = "comment text"

class SongStatsFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.SongStats

    song = factory.SubFactory(SongFactory)

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

class GenreFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Genre

    count=0
    name='Technomatica'
    group='Electronica'