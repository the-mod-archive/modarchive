from django.urls import path
from django.views.generic import ListView

from artists.models import Artist
from artists.views.artist_view import ArtistView

urlpatterns = [
    path('', ListView.as_view(template_name='artist_list.html', model=Artist), {}, 'artists'),
    path('<int:pk>/', ArtistView.as_view(), {}, 'view_artist')
]