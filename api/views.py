import os
import requests
from rest_framework import viewsets, generics, filters, pagination
from rest_framework.exceptions import ValidationError
from django.contrib.postgres.search import SearchVector, SearchQuery
from django.db.models import F
from django.views import View
from django.conf import settings
from django.http import HttpResponse, Http404, StreamingHttpResponse

from songs.models import Song
from artists.models import Artist
from .serializers import SongSerializer, ArtistSerializer, SongSearchResultSerializer

class SongViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Song.objects.all()
    serializer_class = SongSerializer

class ArtistViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Artist.objects.all()
    serializer_class = ArtistSerializer

class StandardResultsSetPagination(pagination.PageNumberPagination):
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 100

class SongSearchAPIView(generics.ListAPIView):
    search_fields = ['title']
    filter_backends = (filters.SearchFilter,)
    serializer_class = SongSearchResultSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        query = self.request.query_params.get('query')
        if not query:
            raise ValidationError("The 'query' parameter is required.")

        file_format = self.request.query_params.get('file_format')
        genre = self.request.query_params.get('genre')
        license_filter = self.request.query_params.get('license')

        queryset = Song.objects.annotate(
            search=SearchVector('title_vector'),
        ).filter(
            search=SearchQuery(query)
        ).annotate(
            relevance=F('search')
        ).order_by('-relevance')

        if file_format:
            queryset = queryset.filter(format=file_format)

        if genre:
            queryset = queryset.filter(genre=genre)

        if license_filter:
            queryset = queryset.filter(license=license_filter)

        return queryset

class SongDownloadView(View):
    def get(self, request, *args, **kwargs):
        pk = kwargs.get('pk')
        song = Song.objects.get(pk=pk)
        
        download_strategy = settings.DOWNLOAD_STRATEGY

        # This is only useful for local development when you don't have the song stored
        # It redirects to the live server: we will eventually remove this path
        if download_strategy == 'redirect':
            remote_url = f'https://api.modarchive.org/downloads.php?moduleid={song.legacy_id}&zip=1'
            remote_response = requests.get(remote_url, timeout=10)

            if remote_response.status_code != 200:
                raise Http404("Remote file not found")

            response = StreamingHttpResponse(
                remote_response.iter_content(chunk_size=8192),
                content_type='application/zip'
            )
            response['Content-Disposition'] = f'attachment; filename="{song.filename}.zip"'
            return response
        
        local_file_path = song.get_archive_path()

        if not os.path.exists(local_file_path):
            raise Http404("File not found")

        stats = song.get_stats()
        stats.downloads = F('downloads') + 1
        stats.save()

        # Serve the file as a response
        with open(local_file_path, 'rb') as file:
            response = HttpResponse(file.read(), content_type='application/zip')
            response['Content-Disposition'] = f'attachment; filename="{song.filename}.zip"'
            return response
