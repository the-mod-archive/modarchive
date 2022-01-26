from django.db import models
from songs.models import Song

class Artist(models.Model):
    legacy_id=models.IntegerField(null=True)
    key=models.CharField(max_length=32, db_index=True)
    name=models.CharField(max_length=64)
    songs=models.ManyToManyField(Song)
    create_date=models.DateTimeField(auto_now_add=True)
    update_date=models.DateTimeField(auto_now=True)