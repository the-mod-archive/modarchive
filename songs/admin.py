from django.contrib import admin
from django.http import Http404
from django.shortcuts import render, redirect
from django.urls import path
from songs import models, forms
from artists.models import Artist

class ArtistInline(admin.TabularInline):
    model = Artist.songs.through

@admin.register(models.Song)
class SongAdmin(admin.ModelAdmin):
    list_display = ("pk", "title", "clean_title", "filename")
    search_fields = ("title__startswith", )
    exclude = ("search_document",)
    form = forms.AdminSongForm
    inlines = [ArtistInline]

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('<int:object_id>/merge_song/', self.merge_song, name='merge_song')
        ]
        return my_urls + urls

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

                # Perform the merge logic here
                # ...

                # Redirect to the admin page of the merged song
                merged_song = models.Song.objects.get(pk=song_to_merge_into_id)
                return redirect('admin:songs_song_change', object_id=merged_song.pk)

        return render(
            request,
            merge_song_template,
            {'object_id': object_id, 'merge_song_form': merge_song_form, 'song_to_merge_from': song_to_merge_from},
        )

@admin.register(models.Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("pk", "text", "rating")

@admin.register(models.Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("song", "profile")

@admin.register(models.ArtistComment)
class ArtistCommentAdmin(admin.ModelAdmin):
    list_display = ["song", "profile"]
