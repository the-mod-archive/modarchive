from django.urls import path
from django.views.generic import ListView

from artists.views import artist_view

urlpatterns = [
    path('', artist_view.ArtistListView.as_view(), {}, 'artists'),
    path('<int:pk>/', artist_view.ArtistDetailView.as_view(), {}, 'view_artist'),
    path('<int:pk>/songs', artist_view.ArtistSongsView.as_view(), {}, 'view_artist_songs'),
    path('<int:pk>/comments', artist_view.ArtistCommentsView.as_view(), {}, 'view_artist_comments'),
    path('<int:pk>/favorites', artist_view.ArtistFavoritesView.as_view(), {}, 'view_artist_favorites'),
]