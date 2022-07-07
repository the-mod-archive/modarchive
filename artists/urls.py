from django.urls import path
from django.views.generic import ListView

from artists.models import Artist
from artists.views.artist_view import ArtistView
from artists.views.add_artist_view import AddArtistView

urlpatterns = [
    path('', ListView.as_view(template_name='artist_list.html', model=Artist), {}, 'artists'),
    path('<int:pk>/', ArtistView.as_view(), {}, 'view_artist'),
    path('add/', AddArtistView.as_view(), {}, 'add_artist')
]