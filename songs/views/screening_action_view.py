from django.shortcuts import redirect
from django.views import View
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.utils import timezone

from songs.models import NewSong
from songs import constants

class ScreeningActionView(PermissionRequiredMixin, View):
    template_name = 'screening_action_result.html'
    permission_required = 'songs.can_approve_songs'

    class ScreeningAction:
        CLAIM = constants.CLAIM_KEYWORD
        PRE_SCREEN = constants.PRE_SCREEN_KEYWORD
        PRE_SCREEN_AND_RECOMMEND = constants.PRE_SCREEN_AND_RECOMMEND_KEYWORD

    def post(self, request, *args, **kwargs):
        # Determine action from request, reject if not a valid action
        action = getattr(self.ScreeningAction, request.POST.get('action', '').upper(), None)

        selected_songs = request.POST.getlist('selected_songs')
        songs = NewSong.objects.filter(id__in=selected_songs)

        match action:
            case self.ScreeningAction.CLAIM:
                songs.filter(claimed_by=None).update(claimed_by=request.user.profile, claim_date=timezone.now())
            case self.ScreeningAction.PRE_SCREEN:
                songs.filter(claimed_by=request.user.profile).update(claimed_by=None, claim_date=None, flag=NewSong.Flags.PRE_SCREENED)
            case self.ScreeningAction.PRE_SCREEN_AND_RECOMMEND:
                songs.filter(claimed_by=request.user.profile).update(claimed_by=None, claim_date=None, flag=NewSong.Flags.PRE_SCREENED_PLUS)

        # Redirect to screening view
        return redirect('screening_index')
