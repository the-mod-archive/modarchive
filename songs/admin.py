from django.contrib import admin
from songs.models import Song

@admin.register(Song)
class SongAdmin(admin.ModelAdmin):
    list_display = ("pk", "title", "clean_title", "filename")
    search_fields = ("title__startswith", )