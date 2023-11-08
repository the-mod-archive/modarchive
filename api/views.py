from django.shortcuts import render
from rest_framework import viewsets

from songs import models
from .serializers import SongSerializer

class SongViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.Song.objects.all()
    serializer_class = SongSerializer