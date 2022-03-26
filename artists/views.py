from django.shortcuts import render

from artists.models import Artist

def artist(request, pk):
    if request.method == 'GET':
        artist = Artist.objects.get(pk = pk)
        return render(request, 'artist.html', context={'artist': artist})