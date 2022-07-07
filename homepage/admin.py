from django.contrib import admin

from . import models

@admin.register(models.Profile)
class SongAdmin(admin.ModelAdmin):
    list_display = ("pk", "display_name")