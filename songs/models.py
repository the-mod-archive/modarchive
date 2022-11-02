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

    class Genres(models.IntegerChoices):
        ELECTRONIC_TECHNO = 1, _("Electronic - Techno")
        ELECTRONIC_DANCE = 2, _("Electronic - Dance")
        ELECTRONIC_AMBIENT = 3, _("Electronic - Ambient")
        ELECTRONIC_TRANCE_GENERAL = 4, _("Trance - General")
        ELECTRONIC_OTHER = 5, _("Electronic - Other")
        ELECTRONIC_GENERAL = 6, _("Electronic - General")
        ELECTRONIC_DRUM_AND_BASS = 7, _("Electronic - Drum & Bass")
        ELECTRONIC_HOUSE = 8, _("Electronic - House")
        ELECTRONIC_RAVE = 9, _("Electronic - Rave")
        ELECTRONIC_TRANCE_DREAM = 10, _("Trance - Dream")
        ELECTRONIC_BREAKBEAT = 11, _("Electronic - Breakbeat")
        ELECTRONIC_INDUSTRIAL = 12, _("Electronic - Industrial")
        ELECTRONIC_HARDCORE = 13, _("Electronic - Hardcore")
        ELECTRONIC_CHILLOUT = 14, _("Chillout")
        ELECTRONIC_TRANCE_GOA = 15, _("Trance - Goa")
        ELECTRONIC_JUNGLE = 16, _("Electronic - Jungle")
        ELECTRONIC_TRANCE_ACID = 17, _("Trance - Acid")
        ELECTRONIC_IDM = 18, _("Electronic - IDM")
        ELECTRONIC_PROGRESSIVE = 19, _("Electronic - Progressive")
        ELECTRONIC_GABBER = 20, _("Electronic - Gabber")
        ELECTRONIC_MINIMAL = 21, _("Electronic - Minimal")
        ELECTRONIC_TRANCE_HARD = 22, _("Trance - Hard")
        ELECTRONIC_TRANCE_PROGRESSIVE = 23, _("Trance - Progressive")
        ELECTRONIC_TRANCE_TRIBAL = 24, _("Trance - Tribal")
        DEMO_CHIPTUNE = 25, _("Chiptune")
        DEMO_STYLE = 26, _("Demostyle")
        DEMO_1HRCOMPO = 27, _("One-Hour Compo")
        POP_GENERAL = 28, _("Pop - General")
        POP_SYNTH = 29, _("Pop - Synth")
        POP_SOFT = 30, _("Pop - Soft")
        POP_ROCK_GENERAL = 31, _("Rock - General")
        POP_ROCK_SOFT = 32, _("Rock - Soft")
        POP_ROCK_HARD = 33, _("Rock - Hard")
        POP_FUNK = 34, _("Funk")
        POP_DISCO = 35, _("Disco")
        POP_BALLAD = 36, _("Ballad")
        POP_EASY_LISTENING = 37, _("Easy Listening")
        OTHER_VIDEO_GAME = 38, _("Video Game")
        OTHER_ORCH = 39, _("Orchestral")
        OTHER_CLASSICAL = 40, _("Classical")
        OTHER_PIANO = 41, _("Piano")
        OTHER_FANTASY = 42, _("Fantasy")
        OTHER_SOUNDTRACK = 43, _("Soundtrack")
        OTHER_COMEDY = 44, _("Comedy")
        OTHER_MEDIEVAL = 45, _("Medieval")
        OTHER_SPIRITUAL = 46, _("Spiritual")
        OTHER_RELIGIOUS = 47, _("Religious")
        OTHER_EXPERIMENTAL = 48, _("Experimental")
        OTHER_NEWAGE = 49, _("New Age")
        OTHER_FOLK = 50, _("Folk")
        OTHER_COUNTRY = 51, _("Country")
        OTHER_BLUEGRASS = 52, _("Bluegrass")
        OTHER_WORLD = 53, _("World")
        OTHER_FUSION = 54, _("Fusion")
        OTHER_VOX_MONTAGE = 55, _("Vocal Montage")
        OTHER_OTHER = 56, _("Other")
        ALTERNATIVE = 57, _("Alternative")
        ALTERNATIVE_GOTHIC = 58, _("Gothic")
        ALTERNATIVE_PUNK = 59, _("Punk")
        ALTERNATIVE_METAL = 60, _("Metal - General")
        ALTERNATIVE_METAL_EXTREME = 61, _("Metal - Extreme")
        ALTERNATIVE_GRUNGE = 62, _("Grunge")
        JAZZ = 63, _("Jazz - General")
        JAZZ_MODERN = 64, _("Jazz - Modern")
        JAZZ_ACID = 65, _("Jazz - Acid")
        JAZZ_BLUES = 66, _("Blues")
        JAZZ_SWING = 67, _("Swing")
        JAZZ_BIG_BAND = 68, _("Big Band")
        HIP_HOP = 69, _("Hip-Hop")
        REGGAE = 70, _("Reggae")
        R_AND_B = 71, _("R&B")
        SOUL = 72, _("Soul")
        SKA = 73, _("Ska")
        CHRISTMAS = 74, _("Christmas")
        HALLOWEEN = 75, _("Halloween")

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
    genre=models.PositiveSmallIntegerField(choices=Genres.choices, null=True, blank=True, db_index=True)
    title_vector=SearchVectorField(null=True, blank=True)
    instrument_text_vector=SearchVectorField(null=True, blank=True)
    comment_text_vector=SearchVectorField(null=True, blank=True)
    create_date=models.DateTimeField(auto_now_add=True)
    update_date=models.DateTimeField(auto_now=True)

    def get_title(self):
        if (self.clean_title):
            return self.clean_title
        return self.title

    def is_own_song(self, profile_id):
        return self.artist_set.all().filter(profile_id=profile_id).exists()

    def has_commented(self, profile_id):
        return self.comment_set.all().filter(profile_id=profile_id).exists()

    def has_artist_commented(self, profile_id):
        return self.artistcomment_set.all().filter(profile_id=profile_id).exists()

    def can_user_leave_comment(self, profile_id):
        return not self.is_own_song(profile_id) and not self.has_commented(profile_id)

    def display_file_size(self):
        if self.file_size >= 1000000:
            return f'{"{:.2f}".format(self.file_size / 1000000)} MB'
        elif self.file_size >= 10000:
            return f'{"{:.2f}".format(self.file_size / 1000)} KB'
        
        return f'{self.file_size} bytes'

    def get_stats(self):
        if (hasattr(self, 'songstats')):
            return self.songstats

        return SongStats.objects.create(song=self)

    class Meta:
        indexes = [
            GinIndex(fields=['title_vector', 'instrument_text_vector', 'comment_text_vector'])
        ]

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

class ArtistComment(models.Model):
    class Meta:
        unique_together = (('profile', 'song'))
        verbose_name_plural = 'artist comments'
        db_table = 'songs_artist_comments'

    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    song = models.ForeignKey(Song, on_delete=models.CASCADE)
    text = models.TextField(max_length=5000)
    create_date = models.DateTimeField(auto_now_add=True)
    update_date=models.DateTimeField(auto_now=True)

class Favorite(models.Model):
    class Meta:
        unique_together = (('profile', 'song'))

    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    song = models.ForeignKey(Song, on_delete=models.CASCADE)
    create_date = models.DateTimeField(auto_now_add=True)