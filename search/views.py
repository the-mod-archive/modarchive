from django.db.models import F, Value, CharField
from django.shortcuts import render
from django.contrib.postgres.search import SearchRank
from django.views.generic import View

from artists.models import Artist
from songs.models import Song
from . import forms

class QuickSearchView(View):
    def search_song_title(self, query, should_search):
        rank_annotation = SearchRank(F('title_vector'), query)
        
        if not should_search:
            return Song.objects.annotate(
                type=Value('empty', output_field=CharField()),
                rank=rank_annotation
            ).values('pk', 'type', 'rank').none()

        return Song.objects.annotate(
            type=Value('song', output_field=CharField()),
            rank=rank_annotation
        ).filter(
            title_vector=query
        ).values('pk', 'type', 'rank')

    def search_artist_name(self, query, should_search):
        rank_annotation = SearchRank(F('search_document'), query)
        
        if not should_search:
            return Artist.objects.annotate(
                type=Value('empty', output_field=CharField()),
                rank=rank_annotation
            ).values('pk', 'type', 'rank').none()

        return Artist.objects.annotate(
            type=Value('artist', output_field=CharField()),
                    rank=rank_annotation
                ).filter(
                    search_document=query
            ).values('pk', 'type', 'rank')

    def get(self, request, *args, **kwargs):
        query = request.GET.get('query')
        should_search_songs = request.GET.get('songs')
        should_search_artists = request.GET.get('artists')

        if not query:
            return render(request, 'search_results.html', {'search_results': [], 'form': forms.SearchForm()})

        search_form = forms.SearchForm(request.GET)

        song_query_set = self.search_song_title(query, should_search_songs)
        artist_query = self.search_artist_name(query, should_search_artists)

        merged_query_set = song_query_set.union(artist_query).order_by('-rank')

        to_fetch = {}
        fetched = {}
        
        for d in merged_query_set:
            to_fetch.setdefault(d['type'], set()).add(d['pk'])

        for key, model in (('song', Song), ('artist', Artist)):
            ids = to_fetch.get(key) or []
            objects = model.objects.filter(pk__in=ids)
            for obj in objects:
                fetched[(key, obj.pk)] = obj

        final_results = []
        for d in merged_query_set:
            item = fetched.get((d['type'], d['pk'])) or None
            if item:
                item.original_dict = d
            final_results.append({'type': d['type'], 'item': item}) 

        return render(request, 'search_results.html', {
            'search_results': final_results,
            'form': search_form
        })

class AdvancedSearchView(View):
    def get(self, request, *args, **kwargs):
        if not request.GET.get('query'):
            return render(request, 'advanced_search_results.html', {'search_results': [], 'form': forms.AdvancedSearchForm()})
        
        form = forms.AdvancedSearchForm(request.GET)

        if not form.is_valid():
            return render(request, 'advanced_search_results.html', {'search_results': [], 'form': form})

        query = form.cleaned_data['query']
        format = form.cleaned_data['format']
        license = form.cleaned_data['license']
        genre = form.cleaned_data['genre']

        # Query songs by title
        rank_annotation = SearchRank(F('title_vector'), query)

        song_query_results = Song.objects.annotate(
            type=Value('song', output_field=CharField()),
            rank=rank_annotation
        ).filter(
            title_vector=query
        ).order_by('-rank')

        # Filter by format, if applicable
        if format:
            song_query_results = song_query_results.filter(format__in=format)

        # Filter by license, if applicable
        if license:
            song_query_results = song_query_results.filter(license__in=license)

        # Filter by genre, if applicable
        if genre:
            song_query_results = song_query_results.filter(genre__in=genre)

        return render(request, 'advanced_search_results.html', {
            'search_results': song_query_results,
            'form': form
        })

def search(request):
    query = request.GET.get('q')
    type = request.GET.get('type')
    
    def should_get_results_for_type(type_requested_in_query, type):
        if (type_requested_in_query is None or type == type_requested_in_query):
            return True
        return False

    if query:
        rank_annotation = SearchRank(F('search_document'), query)
        
        query_set = Song.objects.annotate(
            type=Value('empty', output_field=CharField()),
            rank=rank_annotation
        ).values('pk', 'type', 'rank').none()

        if (should_get_results_for_type(type, 'song')):
            query_set = query_set.union(
                Song.objects.annotate(
                    type=Value('song', output_field=CharField()),
                    rank=rank_annotation
                ).filter(
                    search_document=query
                ).values('pk', 'type', 'rank')
            )

        if (should_get_results_for_type(type, 'artist')):
            query_set = query_set.union(
                Artist.objects.annotate(
                    type=Value('artist', output_field=CharField()),
                    rank=rank_annotation
                ).filter(
                    search_document=query
                ).values('pk', 'type', 'rank')
            )

        sorted_query_set = query_set.order_by('-rank')

        to_fetch = {}
        fetched = {}
        
        for d in sorted_query_set:
            to_fetch.setdefault(d['type'], set()).add(d['pk'])

        for key, model in (('song', Song), ('artist', Artist)):
            ids = to_fetch.get(key) or []
            objects = model.objects.filter(pk__in=ids)
            for obj in objects:
                fetched[(key, obj.pk)] = obj

        final_results = []
        for d in sorted_query_set:
            item = fetched.get((d['type'], d['pk'])) or None
            if item:
                item.original_dict = d
            final_results.append({'type': d['type'], 'item': item})

        return render(request, 'search_results.html', {
            'search_results': final_results
        })