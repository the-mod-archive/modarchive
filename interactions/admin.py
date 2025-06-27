from django.contrib import admin

from interactions import models

@admin.register(models.Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("pk", "text", "rating")

@admin.register(models.Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("song", "profile")

@admin.register(models.ArtistComment)
class ArtistCommentAdmin(admin.ModelAdmin):
    list_display = ["song", "profile"]
