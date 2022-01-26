from django.urls import path
from django.views.generic import DetailView, ListView

from songs.models import Song

urlpatterns = [
    path('', ListView.as_view(template_name='song_list.html', model=Song), {}, 'songs'),
    path('<int:pk>/', DetailView.as_view(template_name='song.html', model=Song), {}, 'view_song')
]