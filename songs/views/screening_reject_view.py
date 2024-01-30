import re
from typing import Any

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import HttpRequest, HttpResponse
from django.views.generic import FormView
from django.shortcuts import render
from django.shortcuts import redirect
from django.contrib import messages
from django.forms import CharField, HiddenInput

from songs import constants, forms
from songs.models import NewSong

class ScreeningRejectView(PermissionRequiredMixin, FormView):
    template_name="screening_reject.html"
    permission_required = 'songs.can_approve_songs'
    form_class = forms.RejectionForm

    def song_ids_valid(self, song_ids) -> bool:
        return song_ids and re.match(r'^(\d+,)*\d+$', song_ids)

    def validate_song_ids(self, raw_song_ids, request):
        if not self.song_ids_valid(raw_song_ids):
            messages.error(request, constants.REJECTION_REQUIRES_IDS)
            return False

        song_ids = [id.strip() for id in raw_song_ids.split(',') if id.strip()]
        new_song_queryset = NewSong.objects.filter(id__in=song_ids)

        # All songs in queryset must be claimed by the current user
        if new_song_queryset.exclude(claimed_by=request.user.profile).exists():
            messages.error(request, constants.REJECTION_ALL_SONGS_MUST_BE_CLAIMED)
            return False

        claimed_queryset = new_song_queryset.filter(claimed_by=request.user.profile)

        if len(claimed_queryset) == 0:
            messages.error(request, constants.REJECTION_REQUIRES_IDS)
            return False

        return claimed_queryset

    def post(self, request: HttpRequest, *args: str, **kwargs: Any) -> HttpResponse:
        form = self.get_form()
        raw_song_ids = form.data.get('song_ids', '')

        claimed_queryset = self.validate_song_ids(raw_song_ids, request)
        if claimed_queryset is False:
            return redirect('screening_index')

        return super().post(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        raw_song_ids = request.GET.get('song_ids', '')

        claimed_queryset = self.validate_song_ids(raw_song_ids, request)
        if claimed_queryset is False:
            return redirect('screening_index')

        # Add a hidden field to the form with the list of song_ids
        claimed_queryset_values = claimed_queryset.values_list('id', flat=True)
        hidden_field = CharField(widget=HiddenInput(), initial=','.join(map(str, claimed_queryset_values)))
        self.form_class.base_fields['song_ids'] = hidden_field

        context = self.get_context_data()
        context['songs'] = claimed_queryset

        return render(request, self.template_name, context)
