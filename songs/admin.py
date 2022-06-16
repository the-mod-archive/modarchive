from django.contrib import admin
from songs.models import Song
from artists.models import Artist

class ArtistInline(admin.TabularInline):
    model = Artist.songs.through

@admin.register(Song)
class SongAdmin(admin.ModelAdmin):
    list_display = ("pk", "title", "clean_title", "filename")
    search_fields = ("title__startswith", )
    exclude = ("search_document",)
    inlines = [ArtistInline]