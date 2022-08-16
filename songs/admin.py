from django.contrib import admin
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

@admin.register(models.Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("pk", "text", "rating")

@admin.register(models.Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("song", "profile")

@admin.register(models.ArtistComment)
class ArtistCommentAdmin(admin.ModelAdmin):
    list_display = ["song", "profile"]