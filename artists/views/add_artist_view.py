from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse
from django.views.generic.edit import CreateView

from artists.forms import CreateArtistForm
from artists.models import Artist

class AddArtistView(PermissionRequiredMixin, CreateView):
    model = Artist
    permission_required = 'artists.add_artist'
    form_class = CreateArtistForm
    template_name = "add_artist.html"

    def get_success_url(self):
        return reverse('view_artist', kwargs={'pk': self.object.pk})