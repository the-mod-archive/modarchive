import factory

from uploads import models
from songs.models import Song

class NewSongFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.NewSong

    format = Song.Formats.S3M
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

class RejectedSongFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.RejectedSong

    is_by_uploader = False
    reason = models.RejectedSong.Reasons.OTHER