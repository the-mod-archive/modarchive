import operator
from functools import reduce

from django.dispatch import receiver

from django.contrib.postgres.search import SearchVector
from django.db.models.signals import post_save

from artists.models import Artist
from songs.models import Song

@receiver(post_save, sender=Song)
def index_song(sender, **kwargs):
    song = kwargs['instance']

    if (song.clean_title):
        title_field = 'clean_title'
    else:
        title_field = 'title'
    
    title_vector=reduce(operator.add, [SearchVector(title_field)])
    instrument_text_vector=reduce(operator.add, [SearchVector('instrument_text')])
    comment_text_vector=reduce(operator.add, [SearchVector('comment_text')])
    
    song.__class__.objects.filter(pk=song.pk).update(
        title_vector=title_vector,
        instrument_text_vector=instrument_text_vector,
        comment_text_vector=comment_text_vector
    )

@receiver(post_save, sender=Artist)
def index_artist(sender, **kwargs):
    artist=kwargs['instance']

    artist.__class__.objects.filter(pk=artist.pk).update(
        search_document=reduce(operator.add, [SearchVector('name')])
    )