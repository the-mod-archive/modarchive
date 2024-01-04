import hashlib
import os

from django.conf import settings
from django.views.generic import FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.files.uploadedfile import TemporaryUploadedFile, InMemoryUploadedFile

from modarchive import file_repository
from songs import forms
from songs.models import NewSong, Song
from songs.mod_info import get_mod_info

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

            modinfo = get_mod_info(file)

            if modinfo is None:
                failed_files.append({'filename': file_name, 'reason': 'Did not recognize this file as a valid mod format.'})
                continue

            # Ensure the song is not in an unsupported format
            mod_format = modinfo.get('format', 'unknown').lower()
            if mod_format in settings.UNSUPPORTED_FORMATS:
                failed_files.append({'filename': file_name, 'reason': 'This format is not currently supported.'})
                continue

            # Rename the file if the extension does not match the format returned by modinfo
            file_ext = os.path.splitext(file_name)[1].lstrip('.')
            if file_ext.lower() != mod_format:
                new_file_name = os.path.splitext(file_name)[0] + '.' + mod_format
                new_file_path = os.path.join(os.path.dirname(file), new_file_name)
                os.rename(file, new_file_path)
                file_name = new_file_name
                file = new_file_path

            if any(char.isupper() for char in file_name) or ' ' in file_name or '__' in file_name:
                new_file_name = file_name.lower().replace(' ', '_')
                while '__' in new_file_name:
                    new_file_name = new_file_name.replace('__', '_')
                new_file_path = os.path.join(os.path.dirname(file), new_file_name)
                os.rename(file, new_file_path)
                file_name = new_file_name
                file = new_file_path

            file_size = os.path.getsize(file)
            with open(file, 'rb') as f:
                md5hash = hashlib.md5(f.read()).hexdigest()

            title = modinfo.get('name', 'untitled')
            song_format = getattr(Song.Formats, modinfo.get('format', 'unknown').upper(), None)

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
                format=song_format,
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
                'format': song_format,
            })
