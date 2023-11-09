from django.shortcuts import render
from rest_framework import viewsets

from songs.models import Song
from artists.models import Artist
from .serializers import SongSerializer, ArtistSerializer

class SongViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Song.objects.all()
    serializer_class = SongSerializer

class ArtistViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Artist.objects.all()
    serializer_class = ArtistSerializer