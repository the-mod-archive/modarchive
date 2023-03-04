from django.urls import path
from songs import views

urlpatterns = [
    path('', views.SongListView.as_view(), {}, 'songs'),
    path('<int:pk>/', views.SongView.as_view(), {}, 'view_song'),
    path('<int:pk>/comment', views.CommentView.as_view(), {}, 'add_comment'),
    path('<int:pk>/download', views.download, name='download_song'),
    path('<int:pk>/add_favorite', views.AddFavoriteView.as_view(), {}, 'add_favorite'),
    path('<int:pk>/remove_favorite', views.RemoveFavoriteView.as_view(), {}, 'remove_favorite'),
    path('<int:pk>/song_details', views.SongDetailsView.as_view(), {}, 'song_details'),
    path('random/', views.RandomSongView.as_view(), {}, 'random_song'),
    path('player/', views.PlayerView.as_view(), {}, 'player'),
    path('browse/license/<str:query>/', views.BrowseSongsByLicenseView.as_view(), name='browse_by_license'),
    path('browse/filename/<str:query>/', views.BrowseSongsByFilenameView.as_view(), name='browse_by_filename'),
    path('browse/genre/<int:query>/', views.BrowseSongsByGenreView.as_view(), name='browse_by_genre'),
    path('browse/rating/<int:query>/', views.BrowseSongsByRatingView.as_view(), name='browse_by_rating')
]