import operator
from functools import reduce

from django.dispatch import receiver

from django.contrib.postgres.search import SearchVector
from django.db import transaction
from django.db.models import Value, TextField
from django.db.models.signals import post_save

from songs.models import Song

@receiver(post_save, sender=Song)
def index_song(sender, **kwargs):
    instance = kwargs['instance']

    if (instance.clean_title):
        title_field = 'clean_title'
    else:
        title_field = 'title'
    
    title_vector=reduce(operator.add, [SearchVector(title_field)])
    text_vector=reduce(operator.add, [SearchVector('instrument_text', 'comment_text')])
    
    instance.__class__.objects.filter(pk=instance.pk).update(
        title_vector=title_vector,
        text_vector=text_vector
    )

@receiver(post_save)
def on_save(sender, **kwargs):
    if not hasattr(sender, 'index_components'):
        return
    transaction.on_commit(make_updater(kwargs['instance']))

def make_updater(instance):
    components = instance.index_components()
    pk = instance.pk

    def on_commit():
        search_vectors = []
        for weight, text in components.items():
            search_vectors.append(
                SearchVector(Value(text, output_field=TextField()), weight=weight)
            )
        instance.__class__.objects.filter(pk=pk).update(
            search_document=reduce(operator.add, search_vectors)
        )

    return on_commit