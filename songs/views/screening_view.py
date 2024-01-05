from django.views.generic import TemplateView
from django.contrib.auth.mixins import PermissionRequiredMixin

class ScreeningView(PermissionRequiredMixin, TemplateView):
    template_name="screening.html"
    permission_required = 'songs.can_approve_songs'
