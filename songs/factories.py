import factory

from songs import models

class SongFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Song

    format = models.Song.Formats.S3M
    filename = factory.Sequence(lambda n: f'song_{n}.s3m')
    title = factory.Sequence(lambda n: f'Song {n}')
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

class SongRedirectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.SongRedirect

    song = factory.SubFactory(SongFactory)
