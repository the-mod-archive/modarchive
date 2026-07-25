from django.core.exceptions import ObjectDoesNotExist
from django.db.models import F
from django.http import Http404
from django.shortcuts import redirect
from django.views import View

from songs.models import Song

class DownloadSongView(View):
    def get(self, request, *args, **kwargs):
        try:
            song = Song.objects.get(pk = kwargs['pk'])
        except ObjectDoesNotExist as e:
            raise Http404 from e

        # Obviously this will not remain in place for the final version of the site, but for now it this is how we download
        download_path = f"https://api.modarchive.org/downloads.php?moduleid={song.legacy_id}#{song.filename}"

        song.downloads_count = F('downloads_count') + 1
        song.save()

        return redirect(download_path)
