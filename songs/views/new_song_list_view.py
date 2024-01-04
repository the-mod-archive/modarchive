from django.contrib.auth.mixins import PermissionRequiredMixin

from homepage.view.common_views import PageNavigationListView
from songs.models import NewSong

class NewSongListView(PermissionRequiredMixin, PageNavigationListView):
    model = NewSong
    template_name = 'new_songs_list.html'
    context_object_name = 'new_songs'
    permission_required = 'songs.can_approve_songs'
    paginate_by = 40
