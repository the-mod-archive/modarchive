from django.db.models import F
from django.shortcuts import render
from django.contrib.postgres.search import SearchQuery, SearchRank

from songs.models import Song

def search(request):
    query = request.GET.get('q')
    if query:
        # Search songs
        search_results = Song.objects.filter(
            search_document=SearchQuery(query)
        ).annotate(
            rank=SearchRank(F('search_document'), query)
        ).order_by('-rank')

        return render(request, 'search_results.html', {
            'search_results': search_results
        })