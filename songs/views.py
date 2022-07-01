from django.shortcuts import redirect
from django.http import Http404
from django.views.generic import DetailView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin

from songs.forms import AddCommentForm
from songs.models import Song

def download(request, pk):
    if request.method == 'GET':
        try:
            song = Song.objects.get(pk = pk)
        except:
            raise Http404

        # Obviously this will not remain in place for the final version of the site, but for now it this is how we download
        download_path = f"https://api.modarchive.org/downloads.php?moduleid={song.legacy_id}#{song.filename}"

        song.songstats.downloads += 1
        song.songstats.save()

        return redirect(download_path)

class SongView(DetailView):
    template_name='song.html'
    model=Song

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if (self.request.user.is_authenticated):
            song = context['song']
            profile_id = self.request.user.profile.id
            context['has_commented'] = song.comment_set.all().filter(profile_id=profile_id).exists()
            context['is_own_song'] = song.artist_set.all().filter(profile_id=profile_id).exists()

        return context

class AddCommentView(LoginRequiredMixin, CreateView):
    form_class = AddCommentForm
    template_name = "add_comment.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)

        song_id = kwargs['pk']
        song = Song.objects.get(id=song_id)
        profile_id = request.user.profile.id
        is_own_song = song.artist_set.all().filter(profile_id=profile_id).exists()
        has_commented = song.comment_set.all().filter(profile_id=profile_id).exists()

        # Storing the song into extra_context to save a database request
        self.extra_context={'song': song}

        if (is_own_song or has_commented):
            return redirect('comment_rejected')

        return super().dispatch(request, *args, **kwargs)

    # Add profile and song ID to the comment in order to save it
    def form_valid(self, form):
        comment_instance = form.save(commit=False)
        comment_instance.profile = self.request.user.profile
        comment_instance.song_id = self.kwargs['pk']
        comment_instance.save()

        return redirect('view_song', self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['song'] = self.extra_context['song'] if self.extra_context['song'] else Song.objects.get(self.kwargs['pk'])
        return context