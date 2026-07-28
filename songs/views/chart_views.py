from django.views.generic import TemplateView

from homepage.views.common_views import PageNavigationListView
from songs.models import Song

class FeaturedSongsView(PageNavigationListView):
    template_name = 'songs_chart.html'
    model = Song

    def get_queryset(self):
        return Song.objects.filter(is_featured=True).order_by('-featured_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['chart'] = 'Featured Songs'
        return context

class TopDownloadsView(PageNavigationListView):
    template_name = 'songs_chart.html'
    model = Song

    def get_queryset(self):
        return Song.objects.order_by('-downloads_count')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['chart'] = 'Most Downloaded Songs'
        return context

class TopRatingsView(PageNavigationListView):
    template_name = 'songs_chart.html'
    model = Song

    def get_queryset(self):
        return Song.objects.order_by('-cumulative_rating').exclude(**{f"cumulative_rating__isnull": True})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['chart'] = 'Top Rated Songs'
        return context

class TopFavoritesView(PageNavigationListView):
    template_name = 'songs_chart.html'
    model = Song

    def get_queryset(self):
        return Song.objects.filter(favorites_count__gte=10).order_by('-favorites_count', 'filename').exclude(**{f"favorites_count__isnull": True})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['chart'] = 'Most Favorited Songs'
        return context