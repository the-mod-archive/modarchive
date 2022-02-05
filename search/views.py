from django.shortcuts import render
from django.contrib.postgres.search import SearchVector

from songs.models import Song

def search(request):
    query = request.GET.get('q')
    if query:
        # Search song titles
        search_results = Song.objects.annotate(searchable=SearchVector('title')).filter(searchable=query)

        return render(request, 'search_results.html', {
            'search_results': search_results
        })