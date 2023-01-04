from django.views.generic import DetailView, ListView

from artists.models import Artist

class ArtistView(DetailView):
    model = Artist
    template_name = 'artist.html'

class ArtistListView(ListView):
    model = Artist
    template_name='artist_list.html'
    queryset=Artist.objects.order_by('-id')[:50]