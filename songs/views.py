import hashlib
import json
import os
import re
import subprocess

from django.db import transaction
from django.db.models import F
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.uploadedfile import TemporaryUploadedFile, InMemoryUploadedFile
from django.shortcuts import redirect, render
from django.http import Http404
from django.views.generic import DetailView, View, TemplateView, ListView, FormView
from django.views.generic.base import ContextMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from random import choice
from django.urls import reverse

from homepage.view.common_views import PageNavigationListView
from modarchive import file_repository
from songs import forms
from songs.models import ArtistComment, Song, Favorite, NewSong

def download(request, pk):
    if request.method == 'GET':
        try:
            song = Song.objects.get(pk = pk)
        except:
            raise Http404

        # Obviously this will not remain in place for the final version of the site, but for now it this is how we download
        download_path = f"https://api.modarchive.org/downloads.php?moduleid={song.legacy_id}#{song.filename}"

        stats = song.get_stats()
        stats.downloads = F('downloads') + 1
        stats.save()

        return redirect(download_path)

class SongListView(ListView):
    template_name='song_list.html'
    model=Song
    queryset=Song.objects.order_by('-id')[:50]

class SongView(DetailView):
    template_name='song_bootstrap.html'
    model=Song

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if (self.request.user.is_authenticated):
            context['is_own_song'] = context['song'].is_own_song(self.request.user.profile.id)
            context['can_comment'] = context['song'].can_user_leave_comment(self.request.user.profile.id)            
            context['is_favorite'] = self.request.user.profile.favorite_set.filter(song_id=context['song'].id).count() > 0
            context['artist_can_comment'] = context['is_own_song'] and not context['song'].has_artist_commented(self.request.user.profile.id)

        return context

class PlayerView(TemplateView):
    template_name='player.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        song_id = self.request.GET.get("song_id")
        song = Song.objects.get(pk = song_id)
        context['song'] = song
        return context

class AddFavoriteView(LoginRequiredMixin, View):
    def is_own_song(self, profile, song_id):
        return hasattr(profile, 'artist') and profile.artist.songs.filter(id=song_id).count() > 0

    def is_already_favorite(self, profile, song_id):
        return Favorite.objects.filter(profile=profile, song_id=song_id).count() > 0

    def get(self, request, *args, **kwargs):
        if (not self.is_own_song(self.request.user.profile, kwargs['pk']) and not self.is_already_favorite(self.request.user.profile, kwargs['pk'])):
            Favorite(profile_id=self.request.user.profile.id, song_id=kwargs['pk']).save()
        return redirect('view_song', kwargs['pk'])

class RemoveFavoriteView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        if (Favorite.objects.filter(profile_id=self.request.user.profile.id, song_id=kwargs['pk']).count() > 0):
            Favorite.objects.get(profile_id=self.request.user.profile.id, song_id=kwargs['pk']).delete()
        return redirect('view_song', kwargs['pk'])

class RandomSongView(View):
    def get(self, request, *args, **kwargs):
        pks = Song.objects.values_list('pk', flat=True)
        random_pk = choice(pks)
        return redirect('view_song', random_pk)

class SongDetailsView(LoginRequiredMixin, ContextMixin, View):
    def dispatch(self, request, *args, **kwargs):
        if (not request.user.is_authenticated):
            return super().dispatch(request, *args, **kwargs)
        
        try:
            song = Song.objects.get(pk=kwargs['pk'])
        except ObjectDoesNotExist:
            raise Http404
        
        if (not song.is_own_song(self.request.user.profile.id)):
            return redirect('view_song', song.id)

        try:
            comment = ArtistComment.objects.get(song=song, profile=request.user.profile)
        except ObjectDoesNotExist:
            comment = ArtistComment(song=song, profile=request.user.profile)

        self.extra_context = {'song': song, 'comment': comment}
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        song = self.extra_context['song']
        comment = self.extra_context['comment']
        song_form = forms.SongDetailsForm(instance=song)
        
        comment_form = forms.AddArtistCommentForm(instance=comment)

        return render(request, 'update_song_details.html', {'object': song, 'form': song_form, 'comment_form': comment_form})

    def post(self, request, *args, **kwargs):
        song = self.extra_context['song']
        comment = self.extra_context['comment']

        song_form = forms.SongDetailsForm(request.POST, instance=song)
        
        # Only create a comment form if text is present in the payload
        if (request.POST['text']):
            comment_form = forms.AddArtistCommentForm(request.POST, instance=comment)
        else:
            comment_form = None

        both_forms_valid = song_form.is_valid() and (not comment_form or comment_form.is_valid())

        if (both_forms_valid):
            song = song_form.save()
            if (comment_form is not None):
                comment_form.save()
            else:
                # If there is a pk but no comment form, that means the user deleted the text, and we should
                # delete the comment
                if (comment.pk):
                    comment.delete()

            return redirect('view_song', song.id)

        return render(request, 'update_song_details.html', {'object': song, 'form': song_form, 'comment_form': comment_form})

class CommentView(LoginRequiredMixin, ContextMixin, View):
    def dispatch(self, request, *args, **kwargs):
        if (not request.user.is_authenticated):
            return super().dispatch(request, *args, **kwargs)

        try:
            song = Song.objects.get(pk=kwargs['pk'])
        except ObjectDoesNotExist:
            raise Http404

        # Users cannot comment on their own song or songs they have already commented on
        if (not song.can_user_leave_comment(request.user.profile.id)):
            return redirect('view_song', kwargs['pk'])

        self.extra_context = {'song': song}

        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        song = self.extra_context['song']
        context = {'song': song}
        
        # If the song does not have a genre, the user leaving the comment may assign it
        if (not song.genre):
            song_form = forms.SongGenreForm(instance=song)
            context['song_form'] = song_form
        
        comment_form = forms.AddCommentForm()
        context['comment_form'] = comment_form
        
        return render(request, 'add_comment.html', context)

    def post(self, request, *args, **kwargs):
        song = self.extra_context['song']
        comment_form = forms.AddCommentForm(request.POST)
        
        # Only update the genre if the genre is not set in the song
        if not song.genre:
            song_form = forms.SongGenreForm(request.POST, instance=song)
        else:
            song_form = None

        # If song_form is None, that means we don't need to validate that form
        both_forms_valid = comment_form.is_valid() and (not song_form or song_form.is_valid())

        if (both_forms_valid):
            with transaction.atomic():
                comment_instance = comment_form.save(commit=False)
                comment_instance.profile = self.request.user.profile
                comment_instance.song_id = song.pk
                comment_form.save()
                # If song_form is not None, that means we have a genre to update on the song
                if song_form:
                    song_form.save()
            return redirect('view_song', kwargs['pk'])
        
        return render(request, 'add_comment.html', {'song': song, 'song_form': song_form, 'comment_form': comment_form})

class BrowseSongsByLicenseView(PageNavigationListView):
    model = Song
    template_name = 'browse_songs.html'
    paginate_by = 40

    def dispatch(self, request, *args, **kwargs):
        query = kwargs['query']
        if query not in dict(Song.Licenses.choices).keys():
            return redirect('home')

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.kwargs['query']
        context['licenses'] = Song.Licenses.choices
        context['options'] = [(code, name, reverse('browse_by_license', kwargs={'query': code})) for code, name in Song.Licenses.choices]
        context['label'] = 'license'
        return context

    def get_queryset(self):
        return Song.objects.filter(license=self.kwargs['query']).order_by('filename')
    
class BrowseSongsByFilenameView(PageNavigationListView):
    model = Song
    template_name = 'browse_songs.html'
    paginate_by = 40

    def dispatch(self, request, *args, **kwargs):
        query = kwargs['query']
        if not re.match(r'^[A-Za-z0-9_]$', query):
            return redirect('home')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.kwargs['query']
        context['options'] = [(char, char, reverse('browse_by_filename', kwargs={'query': char})) for char in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"]
        context['label'] = 'filename'
        return context

    def get_queryset(self):
        return Song.objects.filter(filename__istartswith=self.kwargs['query']).order_by('filename')

class BrowseSongsByGenreView(PageNavigationListView):
    model = Song
    template_name = 'browse_songs.html'
    paginate_by = 40

    def dispatch(self, request, *args, **kwargs):
        query = kwargs['query']

        if query not in dict(Song.Genres.choices).keys():
            return redirect('home')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.kwargs['query']
        context['options'] = [(id, name, reverse('browse_by_genre', kwargs={'query': id})) for id, name in Song.Genres.choices]
        context['label'] = 'genre'

        return context

    def get_queryset(self):
        return Song.objects.filter(genre=self.kwargs['query']).order_by('filename')

class BrowseSongsByRatingView(PageNavigationListView):
    model = Song
    template_name = 'browse_songs.html'
    paginate_by = 40

    def dispatch(self, request, *args, **kwargs):
        query = kwargs['query']

        if not query or query < 1 or query > 9:
            return redirect('home')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.kwargs['query']
        context['options'] = [(score, score, reverse('browse_by_rating', kwargs={'query': score})) for score in [9, 8, 7, 6, 5, 4, 3, 2, 1]]
        context['label'] = 'rating'

        return context

    def get_queryset(self):
        if self.kwargs['query'] == 9:
            return Song.objects.filter(songstats__average_comment_score__gte=9).order_by('-songstats__average_comment_score', 'filename')
        else:
            return Song.objects.filter(songstats__average_comment_score__lt=self.kwargs['query']+1, songstats__average_comment_score__gte=self.kwargs['query']).order_by('-songstats__average_comment_score', 'filename')
        
class UploadView(LoginRequiredMixin, FormView):
    template_name="upload.html"
    form_class = forms.UploadForm

    def form_valid(self, form):
        # Handle the uploaded file and the radio button value here
        if form.cleaned_data['written_by_me'] == 'yes':
            written_by_me = True
        else:
            written_by_me = False
        song_file = form.cleaned_data['song_file']
        
        # Save the uploaded file to a storage backend
        if isinstance(song_file, TemporaryUploadedFile) or isinstance(song_file, InMemoryUploadedFile):
            file_name = song_file.name
            upload_processor = file_repository.UploadProcessor(song_file)
            successful_files = []
            failed_files = []

            if (song_file.size > settings.MAXIMUM_UPLOAD_SIZE):
                failed_files.append({'filename': file_name, 'reason': f'The file was above the maximum allowed size of {settings.MAXIMUM_UPLOAD_SIZE} bytes.'})
            else:
                self.process_files(upload_processor, failed_files, successful_files, written_by_me)

            upload_processor.remove_processing_directory()

        context = self.get_context_data(successful_files=successful_files, failed_files=failed_files)
        return self.render_to_response(context)
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'successful_files' in kwargs:
            context['successful_files'] = kwargs['successful_files']
        if 'failed_files' in kwargs:
            context['failed_files'] = kwargs['failed_files']
        return context
    
    def process_files(self, upload_processor, failed_files, successful_files, written_by_me):
        for file in upload_processor.get_files():
            file_name = os.path.basename(file)

            # Ensure the song's filename length does not exceed the limit
            if len(file_name) > settings.MAXIMUM_UPLOAD_FILENAME_LENGTH:
                failed_files.append({'filename': file_name, 'reason': f'The filename length was above the maximum allowed limit of {settings.MAXIMUM_UPLOAD_FILENAME_LENGTH} characters.'})
                continue

            # Execute modinfo on the file to gather metadata
            modinfo_command = ['modinfo', '--json', file]
            modinfo_output = subprocess.check_output(modinfo_command)
            modinfo = json.loads(modinfo_output)

            file_size = os.path.getsize(file)
            with open(file, 'rb') as f:
                md5hash = hashlib.md5(f.read()).hexdigest()

            title = modinfo.get('name', 'untitled')
            format = getattr(Song.Formats, modinfo.get('format', 'unknown').upper(), None)

            # Ensure that the song is not already in the archive
            songs_in_archive = Song.objects.filter(hash=md5hash)
            if songs_in_archive.count() > 0:
                failed_files.append({'filename': file_name, 'reason': 'An identical song was already found in the archive.'})
                continue

            # Ensure that the song is not already in the processing queue
            songs_in_processing_count = NewSong.objects.filter(hash=md5hash).count()
            if songs_in_processing_count > 0:
                failed_files.append({'filename': file_name, 'reason': 'An identical song was already found in the upload processing queue.'})
                continue

            # Create a NewSong object for the uploaded song
            NewSong.objects.create(
                filename=file_name,
                title=title,
                format=format,
                file_size=file_size,
                channels=int(modinfo.get('channels', '')),
                instrument_text=modinfo.get('instruments', ''),
                comment_text=modinfo.get('comment', ''),
                hash=md5hash,
                pattern_hash=modinfo.get('patterns', ''),
                artist_from_file=modinfo.get('artist', ''),
                uploader_profile=self.request.user.profile,
                uploader_ip_address=self.request.META.get('REMOTE_ADDR'),
                is_by_uploader=written_by_me
            )

            upload_processor.move_into_new_songs(file)

            successful_files.append({
                'filename': file_name,
                'title': title,
                'format': format,
            })

class UploadReportView(LoginRequiredMixin, TemplateView):
    template_name="upload_report.html"