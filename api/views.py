import os
from rest_framework import viewsets, generics, filters, pagination
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.db.models import F, Q
from django.views import View
from django.http import HttpResponse, Http404

from songs.models import Song
from artists.models import Artist
from .serializers import SongSerializer, ArtistSerializer, SongSearchResultSerializer, GenreSerializer, ArtistSearchResultSerializer

class SongViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Song.objects.all()
    serializer_class = SongSerializer

class ArtistViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Artist.objects.all()
    serializer_class = ArtistSerializer

class StandardResultsSetPagination(pagination.PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 100

class SongSearchAPIView(generics.ListAPIView):
    search_fields = ['title']
    filter_backends = (filters.SearchFilter,)
    serializer_class = SongSearchResultSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        title = self.request.query_params.get('title')
        filename = self.request.query_params.get('filename')
        instrument_text = self.request.query_params.get('instrument_text')
        comment_text = self.request.query_params.get('comment_text')

        if not any([title, filename, instrument_text, comment_text]):
            raise ValidationError("At least one of 'title', 'filename', 'instrument_text', or 'comment_text' is required.")

        # Parse min/max parameters
        min_file_size = self.request.query_params.get('min_file_size')
        max_file_size = self.request.query_params.get('max_file_size')
        min_channels = self.request.query_params.get('min_channels')
        max_channels = self.request.query_params.get('max_channels')

        def parse_positive_int(value):
            if value is None:
                return None
            try:
                val = int(value)
                if val <= 0:
                    return -1  # invalid
                return val
            except ValueError:
                return -1

        min_file_size = parse_positive_int(min_file_size)
        max_file_size = parse_positive_int(max_file_size)
        min_channels = parse_positive_int(min_channels)
        max_channels = parse_positive_int(max_channels)

        if min_file_size == -1 or max_file_size == -1 or min_channels == -1 or max_channels == -1:
            return Song.objects.none()

        if (min_file_size and max_file_size and min_file_size > max_file_size) or \
           (min_channels and max_channels and min_channels > max_channels):
            return Song.objects.none()

        file_format = self.request.query_params.get('file_format')
        genre = self.request.query_params.get('genre')
        license_filter = self.request.query_params.get('license')

        queryset = Song.objects.all()

        q_objects = Q()
        relevance_expr = 0

        if title:
            search_title = SearchVector('title_vector')
            rank_title = SearchRank(search_title, SearchQuery(title))
            queryset = queryset.annotate(search_title=search_title, rank_title=rank_title)
            q_objects &= Q(search_title=SearchQuery(title))
            relevance_expr += F('rank_title')

        if instrument_text:
            search_instrument = SearchVector('instrument_text_vector')
            rank_instrument = SearchRank(search_instrument, SearchQuery(instrument_text))
            queryset = queryset.annotate(search_instrument=search_instrument, rank_instrument=rank_instrument)
            q_objects &= Q(search_instrument=SearchQuery(instrument_text))
            relevance_expr += F('rank_instrument')

        if comment_text:
            search_comment = SearchVector('comment_text_vector')
            rank_comment = SearchRank(search_comment, SearchQuery(comment_text))
            queryset = queryset.annotate(search_comment=search_comment, rank_comment=rank_comment)
            q_objects &= Q(search_comment=SearchQuery(comment_text))
            relevance_expr += F('rank_comment')

        if filename:
            q_objects &= Q(filename__icontains=filename)

        if q_objects:
            queryset = queryset.filter(q_objects)
            if relevance_expr:
                queryset = queryset.annotate(relevance=relevance_expr).order_by('-relevance')

        # Apply additional filters
        if file_format:
            queryset = queryset.filter(format=file_format)

        if genre:
            queryset = queryset.filter(genre=genre)

        if license_filter:
            queryset = queryset.filter(license=license_filter)

        if min_file_size:
            queryset = queryset.filter(file_size__gte=min_file_size)

        if max_file_size:
            queryset = queryset.filter(file_size__lte=max_file_size)

        if min_channels:
            queryset = queryset.filter(channels__gte=min_channels)

        if max_channels:
            queryset = queryset.filter(channels__lte=max_channels)

        return queryset

class SongDownloadView(View):
    def get(self, request, *args, **kwargs):
        pk = kwargs.get('pk')
        song = Song.objects.get(pk=pk)
        
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

class GenreListAPIView(generics.ListAPIView):
    serializer_class = GenreSerializer

    def list(self, request, *args, **kwargs):
        genres = [{'id': value, 'text': label} for value, label in Song.Genres.choices]
        serializer = self.get_serializer(genres, many=True)
        return Response(serializer.data)

class ArtistSearchAPIView(generics.ListAPIView):
    serializer_class = ArtistSearchResultSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        name = self.request.query_params.get('name')

        if not name:
            raise ValidationError("The 'name' parameter is required.")

        queryset = Artist.objects.annotate(
            rank=SearchRank('search_document', SearchQuery(name))
        ).filter(
            search_document=SearchQuery(name)
        ).order_by('-rank')

        return queryset
