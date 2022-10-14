from django.db.models import F, Value, CharField
from django.shortcuts import render
from django.contrib.postgres.search import SearchRank
from django.views.generic import View

from artists.models import Artist
from songs.models import Song
from . import forms

class QuickSearchView(View):
    def get(self, request, *args, **kwargs):
        query = request.GET.get('query')

        if not query:
            return render(request, 'search_results.html', {'search_results': []})

        rank_annotation = SearchRank(F('title_vector'), query)

        query_set = Song.objects.annotate(
            type=Value('song', output_field=CharField()),
            rank=rank_annotation
        ).filter(
            title_vector=query
        ).values('pk', 'type', 'rank')

        rank_annotation = SearchRank(F('search_document'), query)

        artist_query = Artist.objects.annotate(
            type=Value('artist', output_field=CharField()),
                    rank=rank_annotation
                ).filter(
                    search_document=query
            ).values('pk', 'type', 'rank')

        merged_query_set = query_set.union(artist_query).order_by('-rank')

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
            'form': forms.SearchForm(request.GET)
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