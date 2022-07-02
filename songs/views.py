from django.shortcuts import redirect
from django.http import Http404
from django.views.generic import DetailView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse

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
            context['can_comment'] = context['song'].can_user_leave_comment(self.request.user.profile.id)

        return context

class AddCommentView(LoginRequiredMixin, CreateView):
    form_class = AddCommentForm
    template_name = "add_comment.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)

        song = Song.objects.get(id=kwargs['pk'])
        if (not song.can_user_leave_comment(request.user.profile.id)):
            return redirect('view_song', kwargs['pk'])

        self.extra_context={'song': song}
        return super().dispatch(request, *args, **kwargs)

    # Add profile and song ID to the comment in order to save it
    def form_valid(self, form):
        comment_instance = form.save(commit=False)
        comment_instance.profile = self.request.user.profile
        comment_instance.song_id = self.kwargs['pk']
        comment_instance.save()

        return super().form_valid(form)
 
    def post(self, request, *args, **kwargs):
        self.success_url = reverse('view_song', kwargs = {'pk': kwargs['pk']})
        return super().post(request, *args, **kwargs)