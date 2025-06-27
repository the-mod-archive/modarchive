from django.db.models import F
from django.shortcuts import redirect, get_object_or_404

from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin

from interactions.models import Favorite
from songs.models import Song

class RemoveFavoriteView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        if Favorite.objects.filter(profile_id=self.request.user.profile.id, song_id=kwargs['pk']).count() > 0:
            Favorite.objects.get(profile_id=self.request.user.profile.id, song_id=kwargs['pk']).delete()
            song = get_object_or_404(Song, pk=kwargs['pk'])
            song_stats = song.get_stats()
            song_stats.total_favorites = F('total_favorites') - 1
            song_stats.save()

        return redirect('view_song', kwargs['pk'])
