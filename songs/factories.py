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

class NewSongFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.NewSong

    format = models.Song.Formats.S3M
    filename = factory.Sequence(lambda n: f'song_{n}.s3m')
    title = factory.Sequence(lambda n: f'Song {n}')
    file_size = 200000
    channels = 16
    hash = "abcdef1234567890"
    pattern_hash = "abcdef1234567890"
    instrument_text = "instrument text"
    comment_text = "comment text"
    artist_from_file = ""
    is_by_uploader = False
    uploader_ip_address = "0.0.0.0"

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

class RejectedSongFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.RejectedSong

    is_by_uploader = False
    reason = models.RejectedSong.Reasons.OTHER

class SongRedirectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.SongRedirect

    song = factory.SubFactory(SongFactory)
