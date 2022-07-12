from django.shortcuts import render
from django.views.generic import DetailView

from artists.models import Artist

class ArtistView(DetailView):
    model = Artist
    template_name = 'artist.html'