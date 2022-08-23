from django.urls import path
from django.views.generic import ListView, TemplateView, DetailView

from songs.models import Song
from songs import views

urlpatterns = [
    path('', ListView.as_view(template_name='song_list.html', model=Song), {}, 'songs'),
    path('<int:pk>/', views.SongView.as_view(), {}, 'view_song'),
    path('<int:pk>/comment', views.AddCommentView.as_view(), {}, 'add_comment'),
    path('<int:pk>/download', views.download, name='download_song'),
    path('<int:pk>/add_favorite', views.AddFavoriteView.as_view(), {}, 'add_favorite'),
    path('<int:pk>/remove_favorite', views.RemoveFavoriteView.as_view(), {}, 'remove_favorite'),
    path('<int:pk>/artist_comment', views.AddArtistCommentView.as_view(), {}, 'add_artist_comment'),
    path('update_artist_comment/<int:pk>', views.UpdateArtistCommentView.as_view(), {}, 'update_artist_comment'),
    path('random/', views.RandomSongView.as_view(), {}, 'random_song'),
    path('player/', views.PlayerView.as_view(), {}, 'player')
]