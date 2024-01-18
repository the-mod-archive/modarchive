from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views.generic import DetailView

from songs.models import NewSong
from songs import constants

class ScreenSongView(PermissionRequiredMixin, DetailView):
    permission_required = 'songs.can_approve_songs'
    model = NewSong
    template_name = 'screen_song.html'
    context_object_name = 'new_song'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['claimed_by_me'] = self.request.user.profile == self.object.claimed_by
        context['claimed_by_other_user'] = self.object.claimed_by is not None and self.request.user.profile != self.object.claimed_by
        if self.object.claimed_by is None:
            context['actions'] = [
                constants.CLAIM_ACTION
            ]
        elif self.object.claimed_by == self.request.user.profile:
            context['actions'] = [
                constants.PRE_SCREEN_ACTION,
                constants.PRE_SCREEN_AND_RECOMMEND_ACTION,
                constants.NEEDS_SECOND_OPINION_ACTION,
                constants.POSSIBLE_DUPLICATE_ACTION
            ]
        elif self.object.claimed_by != self.request.user.profile:
            context['actions'] = []

        return context

    # def get(self, request, pk):
    #     pass
