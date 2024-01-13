from django.shortcuts import redirect
from django.views import View
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.utils import timezone

from songs.models import NewSong

class ScreeningActionView(PermissionRequiredMixin, View):
    template_name = 'screening_action_result.html'
    permission_required = 'songs.can_approve_songs'

    class ScreeningAction:
        APPROVE = 'approve'
        REJECT = 'reject'
        CLAIM = 'claim'

    def post(self, request, *args, **kwargs):
        # Determine action from request, reject if not a valid action
        action = getattr(self.ScreeningAction, request.POST.get('action', '').upper(), None)

        selected_songs = request.POST.getlist('selected_songs')
        songs = NewSong.objects.filter(id__in=selected_songs)

        match action:
            case self.ScreeningAction.CLAIM:
                songs.filter(claimed_by=None).update(claimed_by=request.user.profile, claim_date=timezone.now())
            case _:
                pass

        # Redirect to screening view
        return redirect('screening_index')
