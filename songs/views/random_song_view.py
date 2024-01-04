from random import choice

from django.shortcuts import redirect
from django.views.generic import View

from songs.models import Song

class RandomSongView(View):
    def get(self, request, *args, **kwargs):
        pks = Song.objects.values_list('pk', flat=True)
        random_pk = choice(pks)
        return redirect('view_song', random_pk)
