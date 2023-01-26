from django.core.paginator import Paginator
from django.views.generic import DetailView, ListView

from artists.models import Artist

class PaginatorMixin(DetailView):
    items_per_page = 25
    
    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        data = self.get_all_data(context_data)

        paginator = Paginator(data, self.items_per_page)

        page = self.get_requested_page(self.request)
        paginated_data = paginator.get_page(page)

        context_data['paginator'] = paginated_data
        context_data['has_pages'] = paginator.num_pages > 1
        context_data['range'] = self.get_page_range(page, paginator.num_pages)
        context_data['page'] = page
        context_data['last_page'] = paginator.num_pages

        return context_data

    def get_all_data(self, context):
        pass

    def get_page_range(self, current_page, total_pages):
        if total_pages <= 9:
            return range(1, total_pages + 1)

        min_value = max(1, current_page - 4)
        max_value = min(total_pages, current_page + 4)

        if (max_value - min_value) < 8:
            if (min_value - (8 - (max_value - min_value))) >= 1:
                min_value = min_value - (8 - (max_value - min_value))
            elif (max_value + (8 - (max_value - min_value))) <= total_pages:
                max_value = max_value + (8 - (max_value - min_value))

        return range(min_value, max_value + 1)

    def get_requested_page(self, request):
        try:
            return int(request.GET.get('p', 1))
        except:
            return 1

class ArtistView(DetailView):
    model = Artist
    template_name = 'artist.html'

class ArtistDetailView(DetailView):
    model = Artist
    template_name = "artist_overview.html"

class ArtistSongsView(PaginatorMixin, DetailView):
    model = Artist
    template_name = "artist_songs.html"
    items_per_page = 25

    def get_all_data(self, context):
        return context['artist'].songs.all()

class ArtistFavoritesView(PaginatorMixin, DetailView):
    model = Artist
    template_name = "artist_favorites.html"
    items_per_page = 25

    def get_all_data(self, context):
        return context['artist'].profile.favorite_set.all()

class ArtistCommentsView(PaginatorMixin, DetailView):
    model = Artist
    template_name = "artist_comments.html"
    items_per_page = 15

    def get_all_data(self, context):
        return context['artist'].profile.comment_set.all()

class ArtistListView(ListView):
    model = Artist
    template_name='artist_list.html'
    queryset=Artist.objects.order_by('-id')[:50]