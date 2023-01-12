from django.core.paginator import Paginator
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

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        artist = context_data['artist']
        songs = artist.songs.all()
        paginator = Paginator(songs, 25)

        try:
            page = int(self.request.GET.get('p', 1))
        except:
            page = 1
        paginated_songs = paginator.get_page(page)

        # Min range: 0, or current page - 5, whichever is higher
        min_range = 1 if page <= 5 else page - 5
        # Max range: highest page, or current page + 5, whichever is lower
        max_range = paginator.num_pages if paginator.num_pages - page <= 5 else page + 5

        context_data['songs_paginator'] = paginated_songs
        context_data['has_pages'] = paginator.num_pages > 1
        context_data['range'] = range(min_range, max_range + 1)
        context_data['page'] = page

        return context_data

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