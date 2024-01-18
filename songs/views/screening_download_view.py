import os
from django.conf import settings
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import HttpResponse
from django.views.generic.base import View
from django.shortcuts import get_object_or_404

from songs.models import NewSong

class ScreeningDownloadView(PermissionRequiredMixin, View):
    permission_required = 'songs.can_approve_songs'

    def get(self, request, pk):
        song = get_object_or_404(NewSong, id=pk)
        file_path = os.path.join(settings.NEW_FILE_DIR, f"{song.filename}.zip")

        if os.path.exists(file_path):
            with open(file_path, 'rb') as file:
                response = HttpResponse(file.read(), content_type='application/force-download')
                response['Content-Disposition'] = f'attachment; filename="{song.filename}.zip"'
                return response
        else:
            return HttpResponse("File not found", status=404)
