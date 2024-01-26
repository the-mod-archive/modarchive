from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views.generic import DetailView

from songs.models import NewSong
from songs import constants

class ScreenSongView(PermissionRequiredMixin, DetailView):
    permission_required = 'songs.can_approve_songs'
    model = NewSong
    template_name = 'screen_song.html'
    context_object_name = 'new_song'

    flag_actions_mapping = {
        NewSong.Flags.POSSIBLE_DUPLICATE: [
            constants.PRE_SCREEN_ACTION,
            constants.PRE_SCREEN_AND_RECOMMEND_ACTION,
            constants.NEEDS_SECOND_OPINION_ACTION,
            constants.UNDER_INVESTIGATION_ACTION,
            constants.REJECT_ACTION
        ],
        NewSong.Flags.UNDER_INVESTIGATION: [
            constants.PRE_SCREEN_ACTION,
            constants.PRE_SCREEN_AND_RECOMMEND_ACTION,
            constants.NEEDS_SECOND_OPINION_ACTION,
            constants.POSSIBLE_DUPLICATE_ACTION,
            constants.REJECT_ACTION
        ],
        NewSong.Flags.NEEDS_SECOND_OPINION: [
            constants.PRE_SCREEN_ACTION,
            constants.PRE_SCREEN_AND_RECOMMEND_ACTION,
            constants.POSSIBLE_DUPLICATE_ACTION,
            constants.UNDER_INVESTIGATION_ACTION,
            constants.APPROVE_ACTION,
            constants.APPROVE_AND_FEATURE_ACTION,
            constants.REJECT_ACTION
        ],
        NewSong.Flags.PRE_SCREENED: [
            constants.APPROVE_ACTION,
            constants.APPROVE_AND_FEATURE_ACTION,
            constants.REJECT_ACTION
        ],
        NewSong.Flags.PRE_SCREENED_PLUS: [
            constants.APPROVE_ACTION,
            constants.APPROVE_AND_FEATURE_ACTION,
            constants.REJECT_ACTION
        ]
    }

    claimed_and_no_flag_actions = [
        constants.PRE_SCREEN_ACTION,
        constants.PRE_SCREEN_AND_RECOMMEND_ACTION,
        constants.NEEDS_SECOND_OPINION_ACTION,
        constants.POSSIBLE_DUPLICATE_ACTION,
        constants.UNDER_INVESTIGATION_ACTION,
        constants.APPROVE_ACTION,
        constants.APPROVE_AND_FEATURE_ACTION,
        constants.REJECT_ACTION
    ]

    flag_messages_mapping = {
        NewSong.Flags.NEEDS_SECOND_OPINION: constants.FLAG_MESSAGE_SECOND_OPINION,
        NewSong.Flags.POSSIBLE_DUPLICATE: constants.FLAG_MESSAGE_POSSIBLE_DUPLICATE,
        NewSong.Flags.UNDER_INVESTIGATION: constants.FLAG_MESSAGE_UNDER_INVESTIGATION,
        NewSong.Flags.PRE_SCREENED: constants.FLAG_MESSAGE_PRE_SCREENED,
        NewSong.Flags.PRE_SCREENED_PLUS: constants.FLAG_MESSAGE_PRE_SCREENED_AND_RECOMMENDED
    }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['claimed_by_me'] = self.request.user.profile == self.object.claimed_by
        context['claimed_by_other_user'] = self.object.claimed_by is not None and self.request.user.profile != self.object.claimed_by
        context['flag_message'] = self.flag_messages_mapping.get(self.object.flag, None)
        context['flag_message_class'] = 'success' if self.object.flag in [NewSong.Flags.PRE_SCREENED, NewSong.Flags.PRE_SCREENED_PLUS] else 'warning'
        if self.object.claimed_by is None:
            context['actions'] = [
                constants.CLAIM_ACTION
            ]
        elif self.object.claimed_by == self.request.user.profile:
            if self.object.flagged_by == self.request.user.profile and self.object.flag in [NewSong.Flags.NEEDS_SECOND_OPINION]:
                context['actions'] = []
            else:
                context['actions'] = self.flag_actions_mapping.get(self.object.flag, self.claimed_and_no_flag_actions)
            context['actions'].append(constants.UNCLAIM_ACTION)
        elif self.object.claimed_by != self.request.user.profile:
            context['actions'] = []

        return context
