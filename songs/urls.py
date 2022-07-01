from django.urls import path
from django.views.generic import ListView, TemplateView

from songs.models import Song
from songs.views import download, SongView, AddCommentView

urlpatterns = [
    path('', ListView.as_view(template_name='song_list.html', model=Song), {}, 'songs'),
    path('<int:pk>/', SongView.as_view(), {}, 'view_song'),
    path('<int:pk>/comment', AddCommentView.as_view(), {}, 'add_comment'),
    path('<int:pk>/download', download, name='download_song'),
    path('comment_rejected/', TemplateView.as_view(template_name="comment_rejected.html"), {}, 'comment_rejected')
]