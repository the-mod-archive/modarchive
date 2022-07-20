from django.contrib.auth.models import User

from artists.models import Artist
from songs.models import Song, SongStats, Comment
import factory

class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: 'test_user_%d' % n)
    email = factory.LazyAttribute(lambda o: '%s@example.org' % o.username)

class SongFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Song

    format = Song.Formats.S3M
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
        model = SongStats

    song = factory.SubFactory(SongFactory)

class CommentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Comment

    song = factory.SubFactory(SongFactory)
    rating = 5

class ArtistFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Artist

    @factory.post_generation
    def songs(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for song in extracted:
                self.songs.add(song)

    name = factory.Sequence(lambda n: 'Artist %d' % n)    