from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.postgres.search import SearchVectorField
from django.contrib.postgres.indexes import GinIndex

from homepage.models import Profile

class Song(models.Model):
    class Formats(models.TextChoices):
        MOD = 'MOD', _('Protracker')
        S3M = 'S3M', _('Scream Tracker 3')
        XM = 'XM', _('FastTracker 2')
        IT = 'IT', _('Impulse Tracker')

    class Licenses(models.TextChoices):
        PUBLIC_DOMAIN = 'publicdomain', _('Public Domain')
        NON_COMMERCIAL = 'by-nc', _('Non-commercial')
        NON_COMMERCIAL_NO_DERIVATIVES = 'by-nc-nd', _('Non-commercial No Derivatives')
        NON_COMMERCIAL_SHARE_ALIKE = 'by-nc-sa', _('Non-commercial Share Alike')
        NO_DERIVATIVES = 'by-nd', _('No Derivatives')
        SHARE_ALIKE = 'by-sa', _('Share Alike')
        ATTRIBUTION = 'by', _('Attribution')
        CC0 = 'cc0', _('CC0')

    legacy_id=models.IntegerField(null=True, db_index=True)
    filename=models.CharField(max_length=120, db_index=True)
    title=models.CharField(max_length=120, db_index=True)
    clean_title=models.CharField(max_length=120, null=True, db_index=True, blank=True, help_text="Cleaned-up version of the title for better display and search")
    format=models.CharField(max_length=6, choices=Formats.choices, db_index=True)
    file_size=models.PositiveIntegerField()
    channels=models.PositiveSmallIntegerField()
    instrument_text=models.TextField(max_length=64000)
    comment_text=models.TextField(max_length=64000)
    hash=models.CharField(max_length=33)
    pattern_hash=models.CharField(max_length=16)
    license=models.CharField(max_length=16, choices=Licenses.choices, null=True, blank=True)
    search_document=SearchVectorField(null=True)
    create_date=models.DateTimeField(auto_now_add=True)
    update_date=models.DateTimeField(auto_now=True)

    def get_title(self):
        if (self.clean_title):
            return self.clean_title
        return self.title

    class Meta:
        indexes = [
            GinIndex(fields=['search_document'])
        ]

    def index_components(self):
        return {
            'A': self.title,
            'B': self.filename,
            'C': self.comment_text + ' ' + self.instrument_text
        }

    def __str__(self) -> str:
        return self.get_title()

class SongStats(models.Model):
    song = models.OneToOneField(
        Song,
        on_delete=models.CASCADE,
        primary_key=True
    )
    downloads=models.PositiveIntegerField(default=0)
    total_comments=models.PositiveSmallIntegerField(default=0)
    average_comment_score=models.DecimalField(default=0.0, decimal_places=1, max_digits=3)
    total_reviews=models.PositiveSmallIntegerField(default=0)
    average_review_score=models.DecimalField(default=0.0, decimal_places=1, max_digits=3)

class Comment(models.Model):
    class Ratings(models.IntegerChoices):
        _1 = 1, _("1: Very poor")
        _2 = 2, _("2: Poor")
        _3 = 3, _("3: Listenable")
        _4 = 4, _("4: Good attempt")
        _5 = 5, _("5: Average")
        _6 = 6, _("6: Above average")
        _7 = 7, _("7: Enjoyable")
        _8 = 8, _("8: Very good")
        _9 = 9, _("9: Excellent")
        _10 = 10, _("10: Awesome")

    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, null=True, blank=True)
    song = models.ForeignKey(Song, on_delete=models.CASCADE)
    text = models.TextField(max_length=5000)
    rating = models.PositiveSmallIntegerField(choices=Ratings.choices)
    create_date=models.DateTimeField(auto_now_add=True)