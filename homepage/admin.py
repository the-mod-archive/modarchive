from django.contrib import admin

from . import models

@admin.register(models.Profile)
class SongAdmin(admin.ModelAdmin):
    list_display = ("pk", "display_name")

@admin.register(models.News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ("profile", "headline")
    exclude = ("profile",)

    def save_model(self, request, obj, form, change):
        obj.profile = request.user.profile
        super().save_model(request, obj, form, change)