from django.shortcuts import render
from django.views import View
from django.contrib.auth.mixins import PermissionRequiredMixin

from songs.models import NewSong

class ScreeningActionView(PermissionRequiredMixin, View):
    template_name = 'screening_action_result.html'
    permission_required = 'songs.can_approve_songs'

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')
        selected_songs = request.POST.getlist('selected_songs')
        songs = NewSong.objects.filter(id__in=selected_songs)

        # Perform any desired actions here based on the selected songs and action
        # For now, just render a template displaying the selected songs and action
        return render(request, self.template_name, {'action': action, 'selected_songs': songs})
