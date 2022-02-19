from django.db.models import F, Value, CharField
from django.shortcuts import render
from django.contrib.postgres.search import SearchRank

from artists.models import Artist
from songs.models import Song

def search(request):
    query = request.GET.get('q')
    if query:
        rank_annotation = SearchRank(F('search_document'), query)
        songs_query_set = Song.objects.annotate(
            type=Value('song', output_field=CharField()),
            rank=rank_annotation
        ).filter(
            search_document=query
        ).values('pk', 'type', 'rank')

        artists_query_set = Artist.objects.annotate(
            type=Value('artist', output_field=CharField()),
            rank=rank_annotation
        ).filter(
            search_document=query
        ).values('pk', 'type', 'rank')

        merged_query_set = songs_query_set.union(artists_query_set).order_by('-rank')

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
            'search_results': final_results
        })