from django.shortcuts import redirect, render
from django.http import Http404

from songs.models import Song

def download(request, pk):
    if request.method == 'GET':
        try:
            song = Song.objects.get(pk = pk)
        except:
            raise Http404

        # Obviously this will not remain in place for the final version of the site, but for now it this is how we download
        download_path = f"https://api.modarchive.org/downloads.php?moduleid={song.legacy_id}#{song.filename}"

        song.songstats.downloads += 1
        song.songstats.save()

        return redirect(download_path)