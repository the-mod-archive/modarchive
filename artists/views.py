from django.shortcuts import render

from artists.models import Artist

def artist(request, key):
    if request.method == 'GET':
        artist = Artist.objects.get(key = key)
        return render(request, 'artist.html', context={'artist': artist})