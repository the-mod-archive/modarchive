from django.core.paginator import Paginator
from django.db.models import F, Q, Value, CharField
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
        type = form.cleaned_data['type']

        # Title query
        if 'title' in type:
            title_query_results = Song.objects.annotate(
                rank=SearchRank(F('title_vector'), query)
            ).filter(
                Q(title_vector=query)
            )
        else:
            title_query_results = Song.objects.annotate(
                rank=SearchRank(F('title_vector'), query)
            ).none()

        # Filename query
        if 'filename' in type:
            file_query_results = Song.objects.annotate(
                rank=SearchRank(F('title_vector'), query)
            ).filter(
                Q(filename__icontains=query)
            )
        else:
            file_query_results = Song.objects.none()

        # Comment text query
        if 'comment-text' in type:
            comment_query_results = Song.objects.annotate(
                rank=SearchRank(F('comment_text_vector'), query)
            ).filter(
                comment_text_vector=query
            )
        else:
            comment_query_results = Song.objects.annotate(
                rank=SearchRank(F('comment_text_vector'), query)
            ).none()

        # Instrument text query
        if 'instrument-text' in type:
            instrument_query_results = Song.objects.annotate(
                rank=SearchRank(F('instrument_text_vector'), query)
            ).filter(
                instrument_text_vector=query
            )
        else:
            instrument_query_results = Song.objects.annotate(
                rank=SearchRank(F('instrument_text_vector'), query)
            ).none()

        # Merge all query results
        song_query_results = (title_query_results | comment_query_results | instrument_query_results | file_query_results).order_by('-rank')

        # Filter by format, if applicable
        if format:
            song_query_results = song_query_results.filter(format__in=format)

        # Filter by license, if applicable
        if license:
            song_query_results = song_query_results.filter(license__in=license)

        # Filter by genre, if applicable
        if genre:
            song_query_results = song_query_results.filter(genre__in=genre)

        # File size filtering
        if form.cleaned_data['minSize']:
            song_query_results = song_query_results.filter(file_size__gte=form.cleaned_data['minSize'])

        if form.cleaned_data['maxSize']:
            song_query_results = song_query_results.filter(file_size__lte=form.cleaned_data['maxSize'])

        # Channel filtering
        if form.cleaned_data['minChannels']:
            song_query_results = song_query_results.filter(channels__gte=form.cleaned_data['minChannels'])

        if form.cleaned_data['maxChannels']:
            song_query_results = song_query_results.filter(channels__lte=form.cleaned_data['maxChannels'])

        paginator = Paginator(song_query_results, 25)
        
        page = request.GET.get("page", 1)
        try:
            page = int(page)
            if page < 1:
                page = 1
        except (TypeError, ValueError):
            page = 1
        
        search_results = paginator.get_page(page)

        page_range = paginator.get_elided_page_range(number=page, on_ends=1)

        return render(request, 'advanced_search_results.html', {
            'search_results': search_results,
            'form': form,
            'page_range': page_range
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