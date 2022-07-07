from django.shortcuts import render
from django.views.generic import DetailView

from artists.models import Artist

class ArtistView(DetailView):
    model = Artist
    template_name = 'artist.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if (context['artist'].profile and context['artist'].profile.comment_set.all().count() > 0):
            context['has_comments'] = True

        return context