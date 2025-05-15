from django.contrib import admin
from artists.models import Artist
from songs.admin import ArtistInline

@admin.register(Artist)
class ArtistAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name')
    fields = ('name', 'legacy_id')
    # inlines = (ArtistInline,)
    exclude = ('search_document', 'user', 'profile', 'key')
    search_fields = ['name']