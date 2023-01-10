from django.views.generic import DetailView, ListView

from artists.models import Artist

class ArtistView(DetailView):
    model = Artist
    template_name = 'artist.html'

class ArtistDetailView(DetailView):
    model = Artist
    template_name = "artist_overview.html"

class ArtistSongsView(DetailView):
    model = Artist
    template_name = "artist_songs.html"

class ArtistFavoritesView(DetailView):
    model = Artist
    template_name = "artist_favorites.html"

class ArtistCommentsView(DetailView):
    model = Artist
    template_name = "artist_comments.html"

class ArtistListView(ListView):
    model = Artist
    template_name='artist_list.html'
    queryset=Artist.objects.order_by('-id')[:50]