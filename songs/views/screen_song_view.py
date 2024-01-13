from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views.generic import DetailView

from songs.models import NewSong

class ScreenSongView(PermissionRequiredMixin, DetailView):
    permission_required = 'songs.can_approve_songs'
    model = NewSong
    template_name = 'screen_song.html'
    context_object_name = 'new_song'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['claimed_by_me'] = self.request.user.profile == self.object.claimed_by
        context['claimed_by_other_user'] = self.object.claimed_by is not None and self.request.user.profile != self.object.claimed_by
        return context

    # def get(self, request, pk):
    #     pass
