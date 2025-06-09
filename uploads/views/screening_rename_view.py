import os
import zipfile
import tempfile
from django.views.generic import FormView
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.conf import settings

from uploads import forms
from uploads.models import NewSong
from uploads import constants


class ScreeningRenameView(PermissionRequiredMixin, FormView):
    template_name="screening_rename.html"
    form_class = forms.RenameForm
    permission_required = 'uploads.can_approve_songs'
    model = NewSong

    def form_invalid(self, form):
        form.initial['new_filename'] = self.extra_context['song'].filename
        return render(self.request, self.template_name, self.get_context_data(form=form))

    def form_valid(self, form):
        song = self.extra_context['song']

        if self.rename(song.filename, form.cleaned_data['new_filename']):
            # Remove the old file
            os.remove(os.path.join(settings.NEW_FILE_DIR, f'{song.filename}.zip'))
            # Update the database record
            song.filename = form.cleaned_data['new_filename']
            song.save()
        else:
            # This will only happen if there is a technical issue during the rename.
            messages.error(self.request, constants.RENAME_FAILED)
            return render(self.request, self.template_name, self.get_context_data(form=form))

        return super().form_valid(form)

    def get(self, request, *args, **kwargs):
        song_id = kwargs['pk']
        song = NewSong.objects.get(pk=song_id)

        if song.claimed_by != request.user.profile:
            messages.error(request, constants.RENAME_SCREENING_REQUIRES_CLAIM)
            return redirect('screen_song', pk=song_id)

        context = self.get_context_data()
        context['song'] = song
        context['form'].initial['new_filename'] = song.filename

        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        song_id = kwargs['pk']
        song = NewSong.objects.get(pk=song_id)

        if song.claimed_by != request.user.profile:
            messages.error(request, constants.RENAME_SCREENING_REQUIRES_CLAIM)
            return redirect('screen_song', pk=song_id)

        self.extra_context = {'song': song}

        return super().post(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['instance'] = NewSong.objects.get(pk=self.kwargs['pk'])
        return kwargs

    def get_success_url(self):
        return reverse_lazy('screen_song', kwargs={'pk': self.kwargs['pk']})

    def rename(self, old_filename, new_filename):
        old_zip_file_path = os.path.join(settings.NEW_FILE_DIR, f'{old_filename}.zip')
        new_zip_file_path = os.path.join(settings.NEW_FILE_DIR, f'{new_filename}.zip')

        with zipfile.ZipFile(old_zip_file_path, 'r') as zip_file:
            with tempfile.TemporaryDirectory() as temp_dir:
                try:
                    zip_file.extractall(temp_dir)
                    original_filename = zip_file.namelist()[0]
                    original_file_path = os.path.join(temp_dir, original_filename)
                    new_file_path = os.path.join(temp_dir, new_filename)
                    os.rename(original_file_path, new_file_path)

                    with zipfile.ZipFile(new_zip_file_path, 'w') as new_zip_file:
                        new_zip_file.write(new_file_path, f'{new_filename}')
                except OSError:
                    return False

        return True
