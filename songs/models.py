from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.postgres.search import SearchVectorField
from django.contrib.postgres.indexes import GinIndex

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
    clean_title=models.CharField(max_length=120, null=True, db_index=True)
    format=models.CharField(max_length=6, choices=Formats.choices, db_index=True)
    file_size=models.PositiveIntegerField()
    channels=models.PositiveSmallIntegerField()
    instrument_text=models.TextField(max_length=64000)
    comment_text=models.TextField(max_length=64000)
    hash=models.CharField(max_length=33)
    pattern_hash=models.CharField(max_length=16)
    license=models.CharField(max_length=16, choices=Licenses.choices)
    hits=models.PositiveIntegerField()
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