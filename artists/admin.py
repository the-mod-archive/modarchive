from django.contrib import admin
from artists.models import Artist, ArtistSong

class ArtistSongInlineForArtist(admin.TabularInline):
    model = ArtistSong
    extra = 1
    autocomplete_fields = ['song']

@admin.register(Artist)
class ArtistAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name')
    fields = ('name', 'legacy_id')
    inlines = (ArtistSongInlineForArtist,)
    exclude = ('search_document', 'user', 'profile', 'key')
    search_fields = ['name']
