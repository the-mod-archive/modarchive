from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import redirect, render
from django.views.generic.base import ContextMixin, View
from django.http import Http404

from interactions.forms import AddArtistCommentForm
from interactions.models import ArtistComment
from songs.models import Song
from songs import forms

class SongDetailsView(LoginRequiredMixin, ContextMixin, View):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)

        try:
            song = Song.objects.get(pk=kwargs['pk'])
        except ObjectDoesNotExist as exc:
            raise Http404 from exc

        if not song.is_own_song(self.request.user.profile.id):
            return redirect('view_song', song.id)

        try:
            comment = ArtistComment.objects.get(song=song, profile=request.user.profile)
        except ObjectDoesNotExist:
            comment = ArtistComment(song=song, profile=request.user.profile)

        self.extra_context = {'song': song, 'comment': comment}
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        song = self.extra_context['song']
        comment = self.extra_context['comment']
        song_form = forms.SongDetailsForm(instance=song)

        comment_form = AddArtistCommentForm(instance=comment)

        return render(request, 'update_song_details.html', {'object': song, 'form': song_form, 'comment_form': comment_form})

    def post(self, request, *args, **kwargs):
        song = self.extra_context['song']
        comment = self.extra_context['comment']

        song_form = forms.SongDetailsForm(request.POST, instance=song)

        # Only create a comment form if text is present in the payload
        if request.POST['text']:
            comment_form = AddArtistCommentForm(request.POST, instance=comment)
        else:
            comment_form = None

        both_forms_valid = song_form.is_valid() and (not comment_form or comment_form.is_valid())

        if both_forms_valid:
            song = song_form.save()
            if comment_form is not None:
                comment_form.save()
            else:
                # If there is a pk but no comment form, that means the user deleted the text,
                # and we should delete the comment
                if comment.pk:
                    comment.delete()

            return redirect('view_song', song.id)

        return render(request, 'update_song_details.html', {'object': song, 'form': song_form, 'comment_form': comment_form})
