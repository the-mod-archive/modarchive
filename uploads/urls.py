from django.urls import path

from uploads.views.upload_view import UploadView
from uploads.views.upload_report_view import UploadReportView
from uploads.views.pending_uploads_view import PendingUploadsView
from uploads.views.screening_index_view import ScreeningIndexView
from uploads.views.screening_action_view import ScreeningActionView
from uploads.views.screen_song_view import ScreenSongView
from uploads.views.screening_download_view import ScreeningDownloadView
from uploads.views.screening_reject_view import ScreeningRejectView
from uploads.views.screening_rename_view import ScreeningRenameView

urlpatterns = [
    path('upload', UploadView.as_view(), name='upload_songs'),
    path('upload_report', UploadReportView.as_view(), name='upload_report'),
    path('pending_uploads', PendingUploadsView.as_view(), name='pending_uploads'),
    path('screen_songs', ScreeningIndexView.as_view(), name='screening_index'),
    path('screen_songs/action', ScreeningActionView.as_view(), name='screening_action'),
    path('screen_song/<int:pk>/', ScreenSongView.as_view(), name='screen_song'),
    path('screen_song/<int:pk>/download', ScreeningDownloadView.as_view(), name='screening_download'),
    path('screen_songs/reject', ScreeningRejectView.as_view(), name='screening_reject'),
    path('screen_song/<int:pk>/rename', ScreeningRenameView.as_view(), name='screening_rename'),
]
