from django.urls import path
from django.views.generic import TemplateView

from songs.views.song_view import SongView
from songs.views.add_favorite_view import AddFavoriteView
from songs.views.comment_view import CommentView
from songs.views.download_song_view import DownloadSongView
from songs.views.player_view import PlayerView
from songs.views.song_details_view import SongDetailsView
from songs.views.remove_favorite_view import RemoveFavoriteView
from songs.views.random_song_view import RandomSongView
from songs.views.browse_songs_views import (
    BrowseSongsByLicenseView,
    BrowseSongsByFilenameView,
    BrowseSongsByGenreView,
    BrowseSongsByRatingView
)
from songs.views.upload_view import UploadView
from songs.views.upload_report_view import UploadReportView
from songs.views.pending_uploads_view import PendingUploadsView
from songs.views.new_song_list_view import NewSongListView
from songs.views.screening_view import ScreeningView
from songs.views.screening_action_view import ScreeningActionView

urlpatterns = [
    path('', TemplateView.as_view(template_name='song_list.html'), name='songs'),
    path('<int:pk>/', SongView.as_view(), {}, 'view_song'),
    path('<int:pk>/comment', CommentView.as_view(), {}, 'add_comment'),
    path('<int:pk>/download', DownloadSongView.as_view(), name='download_song'),
    path('<int:pk>/add_favorite', AddFavoriteView.as_view(), {}, 'add_favorite'),
    path('<int:pk>/remove_favorite', RemoveFavoriteView.as_view(), {}, 'remove_favorite'),
    path('<int:pk>/song_details', SongDetailsView.as_view(), {}, 'song_details'),
    path('random/', RandomSongView.as_view(), {}, 'random_song'),
    path('player/', PlayerView.as_view(), {}, 'player'),
    path('browse/license/<str:query>/', BrowseSongsByLicenseView.as_view(), name='browse_by_license'),
    path('browse/filename/<str:query>/', BrowseSongsByFilenameView.as_view(), name='browse_by_filename'),
    path('browse/genre/<str:query>/', BrowseSongsByGenreView.as_view(), name='browse_by_genre'),
    path('browse/rating/<int:query>/', BrowseSongsByRatingView.as_view(), name='browse_by_rating'),
    path('upload', UploadView.as_view(), name='upload_songs'),
    path('upload_report', UploadReportView.as_view(), name='upload_report'),
    path('pending_uploads', PendingUploadsView.as_view(), name='pending_uploads'),
    path('view_new_songs', NewSongListView.as_view(), name='view_new_songs'),
    path('screen_songs', ScreeningView.as_view(), name='screen_songs'),
    path('screen_songs/action', ScreeningActionView.as_view(), name='screening_action')
]
