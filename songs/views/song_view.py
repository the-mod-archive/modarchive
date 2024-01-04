from django.views.generic import DetailView
from songs.models import Song

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

        context['stats'] = context['song'].get_stats()

        return context
