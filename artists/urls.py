from django.urls import path
from django.views.generic import ListView

from artists.models import Artist
from artists.views.artist_view import ArtistView, ArtistListView

urlpatterns = [
    path('', ArtistListView.as_view(), {}, 'artists'),
    path('<int:pk>/', ArtistView.as_view(), {}, 'view_artist')
]