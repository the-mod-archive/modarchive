from django.db import models
from songs.models import Song
from django.contrib.postgres.search import SearchVectorField
from django.contrib.postgres.indexes import GinIndex
from django.contrib.auth.models import User

class Artist(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        primary_key=False,
        null=True
    )
    legacy_id=models.IntegerField(null=True)
    key=models.CharField(max_length=32, db_index=True)
    name=models.CharField(max_length=64)
    songs=models.ManyToManyField(Song)
    search_document=SearchVectorField(null=True)
    create_date=models.DateTimeField(auto_now_add=True)
    update_date=models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            GinIndex(fields=['search_document'])
        ]

    def index_components(self):
        return {
            'A': self.name
        }