from django.db.models import F
from django.shortcuts import redirect, get_object_or_404

from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin

from songs.models import Song, Favorite

class AddFavoriteView(LoginRequiredMixin, View):
    def is_own_song(self, profile, song_id):
        return hasattr(profile, 'artist') and profile.artist.songs.filter(id=song_id).count() > 0

    def is_already_favorite(self, profile, song_id):
        return Favorite.objects.filter(profile=profile, song_id=song_id).count() > 0

    def get(self, request, *args, **kwargs):
        if (not self.is_own_song(self.request.user.profile, kwargs['pk']) and not self.is_already_favorite(self.request.user.profile, kwargs['pk'])):
            Favorite(profile_id=self.request.user.profile.id, song_id=kwargs['pk']).save()
            song = get_object_or_404(Song, pk=kwargs['pk'])
            song_stats = song.get_stats()
            song_stats.total_favorites = F('total_favorites') + 1
            song_stats.save()
        return redirect('view_song', kwargs['pk'])
