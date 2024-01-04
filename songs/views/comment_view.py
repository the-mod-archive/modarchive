from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.views.generic.base import ContextMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import View
from django.shortcuts import redirect, render
from django.http import Http404

from songs.models import Song
from songs import forms

class CommentView(LoginRequiredMixin, ContextMixin, View):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)

        try:
            song = Song.objects.get(pk=kwargs['pk'])
        except ObjectDoesNotExist as exc:
            raise Http404 from exc

        # Users cannot comment on their own song or songs they have already commented on
        if not song.can_user_leave_comment(request.user.profile.id):
            return redirect('view_song', kwargs['pk'])

        self.extra_context = {'song': song}

        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        song = self.extra_context['song']
        context = {'song': song}

        # If the song does not have a genre, the user leaving the comment may assign it
        if not song.genre:
            song_form = forms.SongGenreForm(instance=song)
            context['song_form'] = song_form

        comment_form = forms.AddCommentForm()
        context['comment_form'] = comment_form

        return render(request, 'add_comment.html', context)

    def post(self, request, *args, **kwargs):
        song = self.extra_context['song']
        comment_form = forms.AddCommentForm(request.POST)

        # Only update the genre if the genre is not set in the song
        if not song.genre:
            song_form = forms.SongGenreForm(request.POST, instance=song)
        else:
            song_form = None

        # If song_form is None, that means we don't need to validate that form
        both_forms_valid = comment_form.is_valid() and (not song_form or song_form.is_valid())

        if both_forms_valid:
            with transaction.atomic():
                comment_instance = comment_form.save(commit=False)
                comment_instance.profile = self.request.user.profile
                comment_instance.song_id = song.pk
                comment_form.save()
                # If song_form is not None, that means we have a genre to update on the song
                if song_form:
                    song_form.save()
            return redirect('view_song', kwargs['pk'])

        return render(request, 'add_comment.html', {'song': song, 'song_form': song_form, 'comment_form': comment_form})
