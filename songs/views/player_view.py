from django.views.generic import TemplateView
from songs.models import Song

class PlayerView(TemplateView):
    template_name='player.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        song_id = self.request.GET.get("song_id")
        song = Song.objects.get(pk = song_id)
        context['song'] = song
        return context
