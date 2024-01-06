from django.contrib.auth.mixins import PermissionRequiredMixin

from homepage.view.common_views import PageNavigationListView
from songs.models import NewSong

class ScreeningView(PermissionRequiredMixin, PageNavigationListView):
    model = NewSong
    template_name="screening.html"
    permission_required = 'songs.can_approve_songs'
    context_object_name = 'new_songs'
    paginate_by = 40
