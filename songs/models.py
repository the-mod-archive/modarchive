from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.postgres.search import SearchVectorField
from django.contrib.postgres.indexes import GinIndex

from homepage.models import Profile

class Song(models.Model):
    class Formats(models.TextChoices):
        _669 = '669', _('669: Composer 669 / UNIS 669')
        AHX = 'AHX', _('AHX: Abyss\' Highest eXperience, formerly THX')
        AMF = 'AMF', _('AMF: ASYLUM / DSMI')
        AMS = 'AMS', _('AMS: Extreme\'s Tracker / Velvet Studio')
        C67 = 'C67', _('C67: CDFM / Composer 670')
        DBM = 'DBM', _('DBM: Digi Booster Pro')
        DIGI = 'DIGI', _('DIGI: Digi Booster')
        DMF = 'DMF', _('DMF: X-Tracker')
        DSM = 'DSM', _('DSM: DSIK')
        DSYM = 'DSYM', _('DSYM: Digital Symphony')
        DTM = 'DTM', _('DTM: Digital Tracker / Digital Home Studio')
        FAR = 'FAR', _('FAR: Farandole Composer')
        FMT = 'FMT', _('FMT: FM Tracker')
        GDM = 'GDM', _('GDM: BWSB Sound System')
        HVL = 'HVL', _('HVL: HivelyTracker')
        IMF = 'IMF', _('IMF: Imago Orpheus')
        IT = 'IT', _('IT: Impulse Tracker')
        J2B = 'J2B', _('J2B: Galaxy Sound System')
        MED = 'MED', _('MED: Octamed')
        MDL = 'MDL', _('MDL: Digitrakker')
        MO3 = 'MO3', _('MO3: Compressed Module')
        MOD = 'MOD', _('MOD: Protracker, Generic MOD')
        MPTM = 'MPTM', _('MPTM: OpenMPT')
        MT2 = 'MT2', _('MT2: MadTracker 2')
        MTM = 'MTM', _('MTM: Multi Tracker')
        OKT = 'OKT', _('OKT: Oktalyzer')
        PLM = 'PLM', _('PLM: Disorder Tracker 2')
        PSM = 'PSM', _('PSM: Epic MegaGames MASI')
        PTM = 'PTM', _('PTM: PolyTracker')
        S3M = 'S3M', _('S3M: Scream Tracker 3')
        SFX = 'SFX', _('SFX: SoundFX / MultiMedia Sound')
        STM = 'STM', _('STM: Scream Tracker')
        STP = 'STP', _('STP: SoundTracker Pro II')
        STX = 'STX', _('STX: Scream Tracker Music Interface Kit')
        SymMOD = 'SymMOD', _('SymMOD: Symphonie / Symphonie Pro')
        ULT = 'ULT', _('ULT: UltraTracker')
        UMX = 'UMX', _('UMX: Unreal Music')
        XM = 'XM', _('XM: FastTracker 2')

    class Licenses(models.TextChoices):
        PUBLIC_DOMAIN = 'publicdomain', _('Public Domain')
        NON_COMMERCIAL = 'by-nc', _('Non-commercial')
        NON_COMMERCIAL_NO_DERIVATIVES = 'by-nc-nd', _('Non-commercial No Derivatives')
        NON_COMMERCIAL_SHARE_ALIKE = 'by-nc-sa', _('Non-commercial Share Alike')
        NO_DERIVATIVES = 'by-nd', _('No Derivatives')
        SHARE_ALIKE = 'by-sa', _('Share Alike')
        ATTRIBUTION = 'by', _('Attribution')
        CC0 = 'cc0', _('CC0')

    legacy_id=models.IntegerField(null=True, db_index=True, blank=True)
    filename=models.CharField(max_length=120, db_index=True)
    title=models.CharField(max_length=120, db_index=True)
    clean_title=models.CharField(max_length=120, null=True, db_index=True, blank=True, help_text="Cleaned-up version of the title for better display and search")
    format=models.CharField(max_length=6, choices=Formats.choices, db_index=True)
    file_size=models.PositiveIntegerField()
    channels=models.PositiveSmallIntegerField()
    instrument_text=models.TextField(max_length=64000, blank=True, null=True)
    comment_text=models.TextField(max_length=64000, blank=True, null=True)
    hash=models.CharField(max_length=33)
    pattern_hash=models.CharField(max_length=16)
    license=models.CharField(max_length=16, choices=Licenses.choices, null=True, blank=True)
    search_document=SearchVectorField(null=True, blank=True)
    create_date=models.DateTimeField(auto_now_add=True)
    update_date=models.DateTimeField(auto_now=True)

    def get_title(self):
        if (self.clean_title):
            return self.clean_title
        return self.title

    def can_user_leave_comment(self, profile_id):
        is_own_song = self.artist_set.all().filter(profile_id=profile_id).exists()
        has_commented = self.comment_set.all().filter(profile_id=profile_id).exists()
        return not is_own_song and not has_commented

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
    create_date = models.DateTimeField(auto_now_add=True)

class Favorite(models.Model):
    class Meta:
        unique_together = (('profile', 'song'))

    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    song = models.ForeignKey(Song, on_delete=models.CASCADE)
    create_date = models.DateTimeField(auto_now_add=True)