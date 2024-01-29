from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views.generic import View
from django.shortcuts import render
from django.shortcuts import redirect
from django.contrib import messages

from songs import constants
from songs.models import NewSong

class ScreeningRejectView(PermissionRequiredMixin, View):
    template_name="screening_reject.html"
    permission_required = 'songs.can_approve_songs'

    def get(self, request, *args, **kwargs):
        raw_song_ids = request.GET.get('song_ids', '')
        song_ids = [id.strip() for id in raw_song_ids.split(',') if id.strip()]

        if len(song_ids) == 0:
            messages.error(request, constants.REJECTION_REQUIRES_IDS)
            return redirect('screening_index')

        new_song_queryset = NewSong.objects.filter(id__in=song_ids)

        # All songs in queryset must be claimed by current user
        if new_song_queryset.exclude(claimed_by=request.user.profile).exists():
            messages.error(request, constants.REJECTION_ALL_SONGS_MUST_BE_CLAIMED)
            return redirect('screening_index')

        return render(request, self.template_name)
