from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin

from songs.models import NewSong

class PendingUploadsView(LoginRequiredMixin, ListView):
    model = NewSong
    template_name = 'pending_uploads.html'
    context_object_name = 'pending_uploads'

    def get_queryset(self):
        return NewSong.objects.filter(uploader_profile=self.request.user.profile)
