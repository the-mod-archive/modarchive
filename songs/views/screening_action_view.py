from django.contrib import messages
from django.db.models import Q
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
        NEEDS_SECOND_OPINION = constants.NEEDS_SECOND_OPINION_KEYWORD
        POSSIBLE_DUPLICATE = constants.POSSIBLE_DUPLICATE_KEYWORD
        UNDER_INVESTIGATION = constants.UNDER_INVESTIGATION_KEYWORD
        APPROVE = constants.APPROVE_KEYWORD

    def post(self, request, *args, **kwargs):
        # Determine action from request, reject if not a valid action
        action = getattr(self.ScreeningAction, request.POST.get('action', '').upper(), None)

        selected_songs = request.POST.getlist('selected_songs')
        songs = NewSong.objects.filter(id__in=selected_songs)

        match action:
            case self.ScreeningAction.CLAIM:
                songs.filter(
                    claimed_by=None
                ).exclude(
                    Q(flagged_by=request.user.profile, flag=NewSong.Flags.NEEDS_SECOND_OPINION) |
                    Q(flagged_by=request.user.profile, flag=NewSong.Flags.POSSIBLE_DUPLICATE) |
                    Q(flagged_by=request.user.profile, flag=NewSong.Flags.UNDER_INVESTIGATION)
                ).update(
                    claimed_by=request.user.profile,
                    claim_date=timezone.now()
                )
            case self.ScreeningAction.PRE_SCREEN:
                songs.filter(
                    claimed_by=request.user.profile
                ).update(
                    claimed_by=None,
                    claim_date=None,
                    flag=NewSong.Flags.PRE_SCREENED,
                    flagged_by=request.user.profile
                )
            case self.ScreeningAction.PRE_SCREEN_AND_RECOMMEND:
                songs.filter(
                    claimed_by=request.user.profile
                ).update(
                    claimed_by=None,
                    claim_date=None,
                    flag=NewSong.Flags.PRE_SCREENED_PLUS,
                    flagged_by=request.user.profile
                )
            case self.ScreeningAction.NEEDS_SECOND_OPINION:
                songs.filter(
                    claimed_by=request.user.profile
                ).update(
                    claimed_by=None,
                    claim_date=None,
                    flag=NewSong.Flags.NEEDS_SECOND_OPINION,
                    flagged_by=request.user.profile
                )
            case self.ScreeningAction.POSSIBLE_DUPLICATE:
                songs.filter(
                    claimed_by=request.user.profile
                ).update(
                    claimed_by=None,
                    claim_date=None,
                    flag=NewSong.Flags.POSSIBLE_DUPLICATE,
                    flagged_by=request.user.profile
                )
            case self.ScreeningAction.UNDER_INVESTIGATION:
                songs.filter(
                    claimed_by=request.user.profile
                ).update(
                    claimed_by=None,
                    claim_date=None,
                    flag=NewSong.Flags.UNDER_INVESTIGATION,
                    flagged_by=request.user.profile
                )
            case self.ScreeningAction.APPROVE:
                return self.approve_songs(songs, request)

        # Redirect to screening view
        return redirect('screening_index')

    def approve_songs(self, songs, request):
        if songs.filter(claimed_by=request.user.profile).exists():
            if songs.filter(flag=NewSong.Flags.UNDER_INVESTIGATION).exists():
                messages.warning(request, constants.MESSAGE_CANNOT_APPROVE_UNDER_INVESTIGATION)
                return redirect('screen_song', pk=songs[0].id)
            elif songs.filter(flag=NewSong.Flags.POSSIBLE_DUPLICATE).exists():
                messages.warning(request, constants.MESSAGE_CANNOT_APPROVE_POSSIBLE_DUPLICATE)
                return redirect('screen_song', pk=songs[0].id)

        messages.warning(request, constants.MESSAGE_APPROVAL_REQUIRES_CLAIM)
        return redirect('screen_song', pk=songs[0].id)
