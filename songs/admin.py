import os
from django.contrib import admin
from django.http import Http404
from django.shortcuts import render, redirect
from django.urls import path
from django.db.models import F
from django.conf import settings
from django.utils import timezone
from interactions.models import Favorite
from songs import models, forms
from uploads import models as upload_models
from interactions import models as interaction_models
from artists.models import Artist

class ArtistInline(admin.TabularInline):
    model = Artist.songs.through

@admin.register(models.Song)
class SongAdmin(admin.ModelAdmin):
    list_display = ("pk", "title", "clean_title", "filename")
    search_fields = ("title__startswith", )
    exclude = ("search_document",)
    form = forms.AdminSongForm
    # inlines = [ArtistInline]

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('<int:object_id>/merge_song/', self.merge_song, name='merge_song')
        ]
        return my_urls + urls

    def should_create_new_favorite(self, song_to_merge_into, favorite):
        return not song_to_merge_into.favorite_set.filter(profile=favorite.profile).exists() and not song_to_merge_into.is_own_song(favorite.profile_id)

    def merge_favorites(self, song_to_merge_from, song_to_merge_into):
        for favorite in song_to_merge_from.favorite_set.all():
            if self.should_create_new_favorite(song_to_merge_into, favorite):
                Favorite.objects.create(
                    song=song_to_merge_into,
                    profile=favorite.profile
                )
            favorite.delete()

    def should_create_comment(self, song_to_merge_into, comment):
        return not song_to_merge_into.is_own_song(comment.profile_id) and not song_to_merge_into.comment_set.filter(profile=comment.profile).exists()

    def merge_comments(self, song_to_merge_from, song_to_merge_into):
        for comment in song_to_merge_from.comment_set.all():
            if self.should_create_comment(song_to_merge_into, comment):
                interaction_models.Comment.objects.create(
                    text=comment.text,
                    rating=comment.rating,
                    profile=comment.profile,
                    song=song_to_merge_into,
                    create_date=comment.create_date
                )
            comment.delete()

    def should_merged_featured(self, song_to_merge_from, song_to_merge_into):
        return song_to_merge_from.is_featured and (
            song_to_merge_into.featured_date is None or song_to_merge_from.featured_date < song_to_merge_into.featured_date
        )

    def merge_featured(self, song_to_merge_from, song_to_merge_into):
        if self.should_merged_featured(song_to_merge_from, song_to_merge_into):
            song_to_merge_into.is_featured = True
            song_to_merge_into.featured_date = song_to_merge_from.featured_date
            song_to_merge_into.featured_by = song_to_merge_from.featured_by
            song_to_merge_into.save()

    def update_downloads(self, song_to_merge_from, song_to_merge_into):
        downloads = song_to_merge_from.get_stats().downloads
        stats = song_to_merge_into.get_stats()
        stats.downloads=F('downloads') + downloads
        stats.save()

    def finalize_merge(self, song_to_merge_from: models.Song, song_to_merge_into):
        # Move the file to the removed files folder
        source_path = song_to_merge_from.get_archive_path()
        destination_path = os.path.join(settings.REMOVED_FILE_DIR, f'{song_to_merge_from.filename}.zip')
        os.rename(source_path, destination_path)

        self.update_downloads(song_to_merge_from, song_to_merge_into)

        # Merge artists
        for artist in song_to_merge_from.artist_set.all():
            song_to_merge_into.artist_set.add(artist)

        self.merge_favorites(song_to_merge_from, song_to_merge_into)
        self.merge_comments(song_to_merge_from, song_to_merge_into)
        self.merge_featured(song_to_merge_from, song_to_merge_into)

        # Create a redirect
        models.SongRedirect.objects.create(
            old_song_id=song_to_merge_from.id,
            song_id=song_to_merge_into.id
        )

        # Create a rejected song entry
        upload_models.RejectedSong.objects.create(
            reason=upload_models.RejectedSong.Reasons.ALREADY_EXISTS,
            message=f'TIDY-UP MERGED. {song_to_merge_from.filename} already exists as {song_to_merge_into.filename} on the archive.',
            hash=song_to_merge_from.hash,
            pattern_hash=song_to_merge_from.pattern_hash,
            filename=song_to_merge_from.filename,
            filename_unzipped=song_to_merge_from.filename_unzipped,
            title=song_to_merge_from.title,
            format=song_to_merge_from.format,
            file_size=song_to_merge_from.file_size,
            channels=song_to_merge_from.channels,
            comment_text=song_to_merge_from.comment_text,
            instrument_text=song_to_merge_from.instrument_text,
            uploader_profile=song_to_merge_from.uploaded_by,
            is_by_uploader=False,
            rejected_date=timezone.now(),
            create_date=song_to_merge_from.create_date
        )

        # Remove the old song
        song_to_merge_from.delete()

    def merge_song(self, request, object_id):
        merge_song_form = forms.MergeSongForm()
        song_to_merge_from = models.Song.objects.get(pk=object_id)
        merge_song_template = 'admin/songs/song/merge_song_form.html'

        if request.method == 'POST':
            merge_song_form = forms.MergeSongForm(request.POST)
            if merge_song_form.is_valid():
                song_to_merge_into_id = merge_song_form.cleaned_data['song_to_merge_into_id']

                if song_to_merge_into_id == object_id:
                    merge_song_form.add_error(
                        'song_to_merge_into_id',
                        "You cannot merge a song into itself."
                    )
                    return render(
                        request,
                        merge_song_template,
                        {'object_id': object_id, 'merge_song_form': merge_song_form, 'song_to_merge_from': song_to_merge_from}
                    )

                try:
                    song_to_merge_into = models.Song.objects.get(pk=song_to_merge_into_id)
                except models.Song.DoesNotExist as e:
                    raise Http404("Song with the provided ID does not exist.") from e

                if not merge_song_form.cleaned_data['commit']:
                    commit_merge_song_form = forms.CommitMergeSongForm(
                        initial={'song_to_merge_into_id': song_to_merge_into_id}
                    )
                    return render(
                        request,
                        merge_song_template,
                        {
                            'object_id': object_id,
                            'merge_song_form': commit_merge_song_form,
                            'song_to_merge_from': song_to_merge_from,
                            'song_to_merge_into': song_to_merge_into
                        }
                    )

                self.finalize_merge(song_to_merge_from, song_to_merge_into)
                return redirect('admin:songs_song_change', object_id=song_to_merge_into.pk)

        return render(
            request,
            merge_song_template,
            {'object_id': object_id, 'merge_song_form': merge_song_form, 'song_to_merge_from': song_to_merge_from},
        )
