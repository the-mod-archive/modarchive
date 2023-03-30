from django.db import models
from django.utils import timezone
from homepage.models import Profile
from songs.models import Song
from django.contrib.postgres.fields import CICharField
from django.contrib.postgres.search import SearchVectorField
from django.contrib.postgres.indexes import GinIndex
from django.contrib.auth.models import User

class Artist(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        primary_key=False,
        null=True,
        blank=True
    )
    profile = models.OneToOneField(
        Profile,
        on_delete=models.SET_NULL,
        primary_key=False,
        null=True,
        blank=True
    )
    legacy_id=models.IntegerField(null=True, blank=True, help_text="User ID from the legacy Mod Archive site", db_index=True)
    key=models.CharField(max_length=32, db_index=True, blank=True)
    name=CICharField(max_length=64, unique=True)
    songs=models.ManyToManyField(Song, blank=True)
    search_document=SearchVectorField(null=True)
    create_date=models.DateTimeField(default=timezone.now)
    update_date=models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            GinIndex(fields=['search_document'])
        ]

    def index_components(self):
        return {
            'A': self.name
        }

    def __str__(self):
        return self.name