from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views.generic import DetailView

from songs.models import NewSong

class ScreenSongView(PermissionRequiredMixin, DetailView):
    permission_required = 'songs.can_approve_songs'
    model = NewSong
    template_name = 'screen_song.html'
    context_object_name = 'new_song'

    # def get(self, request, pk):
    #     pass
