import hashlib
import os

from django.conf import settings
from django.views.generic import FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.files.uploadedfile import TemporaryUploadedFile, InMemoryUploadedFile

from modarchive import file_repository
from songs import forms, constants
from songs.models import NewSong, Song, RejectedSong
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

            if song_file.size > settings.MAXIMUM_UPLOAD_SIZE:
                self.add_failure(failed_files, file_name, constants.UPLOAD_TOO_LARGE%(settings.MAXIMUM_UPLOAD_SIZE))
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
                self.add_failure(failed_files, file_name, constants.UPLOAD_FILENAME_TOO_LONG%(settings.MAXIMUM_UPLOAD_FILENAME_LENGTH))
                continue

            modinfo = get_mod_info(file)

            if modinfo is None:
                self.add_failure(failed_files, file_name, constants.UPLOAD_UNRECOGNIZED_FORMAT)
                continue

            # Ensure the song is not in an unsupported format
            mod_format = modinfo.get('format', 'unknown').lower()
            if mod_format in settings.UNSUPPORTED_FORMATS:
                self.add_failure(failed_files, file_name, constants.UPLOAD_UNSUPPORTED_FORMAT)
                continue

            file_name, file = self.rename_file(file, file_name, mod_format)
            md5hash = self.get_md5_hash(file)

            if self.song_already_exists(file_name, md5hash, failed_files):
                continue

            song_data = {
                'filename': file_name,
                'title': modinfo.get('name', 'untitled'),
                'format': getattr(Song.Formats, mod_format.upper(), None),
                'file_size': os.path.getsize(file),
                'channels': int(modinfo.get('channels', '')),
                'instrument_text': modinfo.get('instruments', ''),
                'comment_text': modinfo.get('comment', ''),
                'hash': md5hash,
                'pattern_hash': modinfo.get('patterns', ''),
                'artist_from_file': modinfo.get('artist', ''),
                'uploader_profile': self.request.user.profile,
                'uploader_ip_address': self.request.META.get('REMOTE_ADDR'),
                'is_by_uploader': written_by_me
            }

            self.finalize_upload(upload_processor, file, successful_files, song_data)

    def rename_file(self, file, file_name, mod_format):
        # Rename the file if the extension does not match the format returned by modinfo
        file_ext = os.path.splitext(file_name)[1].lstrip('.')
        if file_ext.lower() != mod_format:
            new_file_name = os.path.splitext(file_name)[0] + '.' + mod_format
            new_file_path = os.path.join(os.path.dirname(file), new_file_name)
            os.rename(file, new_file_path)
            file_name = new_file_name
            file = new_file_path

        # Replace whitespace or consecutive underscores with a single underscore
        if any(char.isupper() for char in file_name) or ' ' in file_name or '__' in file_name:
            new_file_name = file_name.lower().replace(' ', '_')
            while '__' in new_file_name:
                new_file_name = new_file_name.replace('__', '_')
            new_file_path = os.path.join(os.path.dirname(file), new_file_name)
            os.rename(file, new_file_path)
            file_name = new_file_name
            file = new_file_path

        return file_name, file

    def song_already_exists(self, file_name, md5hash, failed_files):
        """Returns True if the song already exists in the archive or upload processing 
        queue, and adds a failure message to the list of failed files."""
        # Ensure that the song is not already in the archive
        if Song.objects.filter(hash=md5hash).exists():
            self.add_failure(failed_files, file_name, constants.UPLOAD_DUPLICATE_SONG_IN_ARCHIVE)
            return True

        # Ensure that the song is not already in the processing queue
        if NewSong.objects.filter(hash=md5hash).exists():
            self.add_failure(failed_files, file_name, constants.UPLOAD_DUPLICATE_SONG_IN_PROCESSING_QUEUE)
            return True

        # Ensure that the song was not permanently rejected in the past
        if RejectedSong.objects.filter(hash=md5hash, is_temporary=False).exists():
            self.add_failure(failed_files, file_name, constants.UPLOAD_SONG_PREVIOUSLY_REJECTED)
            return True

        return False

    def finalize_upload(self, upload_processor, file, successful_files, song_data):
        """Moves the file into the upload processing directory and creates a NewSong record"""
        NewSong.objects.create(
            filename=song_data['filename'],
            filename_unzipped=song_data['filename'],
            title=song_data['title'],
            format=song_data['format'],
            file_size=song_data['file_size'],
            channels=song_data['channels'],
            instrument_text=song_data['instrument_text'],
            comment_text=song_data['comment_text'],
            hash=song_data['hash'],
            pattern_hash=song_data['pattern_hash'],
            artist_from_file=song_data['artist_from_file'],
            uploader_profile=song_data['uploader_profile'],
            uploader_ip_address=song_data['uploader_ip_address'],
            is_by_uploader=song_data['is_by_uploader']
        )

        upload_processor.move_into_new_songs(file)

        successful_files.append({
            'filename': song_data['filename'],
            'title': song_data['title'],
            'format': song_data['format'],
        })

    def get_md5_hash(self, file):
        with open(file, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()

    def add_failure(self, failed_files, file_name, reason):
        failed_files.append({'filename': file_name, 'reason': reason})
