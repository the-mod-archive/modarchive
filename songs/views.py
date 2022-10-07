from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import redirect, render
from django.http import Http404
from django.views.generic import DetailView, CreateView, View, UpdateView, TemplateView
from django.views.generic.base import ContextMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from random import choice

from songs import forms
from songs.models import ArtistComment, Song, Favorite

def download(request, pk):
    if request.method == 'GET':
        try:
            song = Song.objects.get(pk = pk)
        except:
            raise Http404

        # Obviously this will not remain in place for the final version of the site, but for now it this is how we download
        download_path = f"https://api.modarchive.org/downloads.php?moduleid={song.legacy_id}#{song.filename}"

        stats = song.get_stats()
        stats.downloads += 1
        stats.save()

        return redirect(download_path)

class SongView(DetailView):
    template_name='song_bootstrap.html'
    model=Song

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if (self.request.user.is_authenticated):
            context['is_own_song'] = context['song'].is_own_song(self.request.user.profile.id)
            context['can_comment'] = context['song'].can_user_leave_comment(self.request.user.profile.id)            
            context['is_favorite'] = self.request.user.profile.favorite_set.filter(song_id=context['song'].id).count() > 0
            context['artist_can_comment'] = context['is_own_song'] and not context['song'].has_artist_commented(self.request.user.profile.id)

        return context

class PlayerView(TemplateView):
    template_name='player.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        song_id = self.request.GET.get("song_id")
        song = Song.objects.get(pk = song_id)
        context['song'] = song
        return context

class AddCommentView(LoginRequiredMixin, CreateView):
    form_class = forms.AddCommentForm
    template_name = "add_comment.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)

        song = Song.objects.get(id=kwargs['pk'])
        if (not song.can_user_leave_comment(request.user.profile.id)):
            return redirect('view_song', kwargs['pk'])

        self.extra_context={'song': song}
        return super().dispatch(request, *args, **kwargs)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.helper.form_action = reverse('add_comment', kwargs=self.kwargs)
        return form

    # Add profile and song ID to the comment in order to save it
    def form_valid(self, form):
        comment_instance = form.save(commit=False)
        comment_instance.profile = self.request.user.profile
        comment_instance.song_id = self.kwargs['pk']

        return super().form_valid(form)
 
    def get_success_url(self):
        return reverse('view_song', kwargs={'pk': self.object.song_id})

class AddFavoriteView(LoginRequiredMixin, View):
    def is_own_song(self, profile, song_id):
        return hasattr(profile, 'artist') and profile.artist.songs.filter(id=song_id).count() > 0

    def is_already_favorite(self, profile, song_id):
        return Favorite.objects.filter(profile=profile, song_id=song_id).count() > 0

    def get(self, request, *args, **kwargs):
        if (not self.is_own_song(self.request.user.profile, kwargs['pk']) and not self.is_already_favorite(self.request.user.profile, kwargs['pk'])):
            Favorite(profile_id=self.request.user.profile.id, song_id=kwargs['pk']).save()
        return redirect('view_song', kwargs['pk'])

class RemoveFavoriteView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        if (Favorite.objects.filter(profile_id=self.request.user.profile.id, song_id=kwargs['pk']).count() > 0):
            Favorite.objects.get(profile_id=self.request.user.profile.id, song_id=kwargs['pk']).delete()
        return redirect('view_song', kwargs['pk'])

class RandomSongView(View):
    def get(self, request, *args, **kwargs):
        pks = Song.objects.values_list('pk', flat=True)
        random_pk = choice(pks)
        return redirect('view_song', random_pk)

class SongDetailsView(LoginRequiredMixin, ContextMixin, View):
    def dispatch(self, request, *args, **kwargs):
        if (not request.user.is_authenticated):
            return super().dispatch(request, *args, **kwargs)
        
        try:
            song = Song.objects.get(pk=kwargs['pk'])
        except ObjectDoesNotExist:
            raise Http404
        
        if (not song.is_own_song(self.request.user.profile.id)):
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
        
        comment_form = forms.AddArtistCommentForm(instance=comment)

        return render(request, 'update_song_details.html', {'object': song, 'form': song_form, 'comment_form': comment_form})

    def post(self, request, *args, **kwargs):
        song = self.extra_context['song']
        comment = self.extra_context['comment']

        song_form = forms.SongDetailsForm(request.POST, instance=song)
        
        # Only create a comment form if text is present in the payload
        if (request.POST['text']):
            comment_form = forms.AddArtistCommentForm(request.POST, instance=comment)
        else:
            comment_form = None

        both_forms_valid = song_form.is_valid() and (not comment_form or comment_form.is_valid())

        if (both_forms_valid):
            song = song_form.save()
            if (comment_form is not None):
                comment_form.save()
            else:
                # If there is a pk but no comment form, that means the user deleted the text, and we should
                # delete the comment
                if (comment.pk):
                    comment.delete()

            return redirect('view_song', song.id)

        return render(request, 'update_song_details.html', {'object': song, 'form': song_form, 'comment_form': comment_form})