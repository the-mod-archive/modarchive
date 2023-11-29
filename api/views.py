from rest_framework import viewsets, generics, filters, pagination
from rest_framework.exceptions import ValidationError
from django.contrib.postgres.search import SearchVector, SearchQuery
from django.db.models import F

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