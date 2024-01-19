from django.core.management.base import BaseCommand

from homepage import legacy_models
from songs.models import Song, SongStats
from .disable_signals import DisableSignals

class Command(BaseCommand):
    help = "Migrate the legacy files table"

    def handle(self, *args, **options):
        with DisableSignals():
            files = legacy_models.Files.objects.using('legacy').all().order_by('id')

            total = len(files)
            counter = 0
            print(f"Starting migrations of {total} files. This process will create all song and song_stats objects.")

            for file in files:
                counter += 1

                if counter % 1000 == 0:
                    print(f"Generated {counter} out of {total} from the legacy files table.")

                self.generate_song(file)

    def generate_song(self, legacy_file):
        # Generate song
        create_date = legacy_file.date if legacy_file.date else legacy_file.timestamp

        song = Song.objects.create(
            legacy_id = legacy_file.id,
            filename = legacy_file.filename,
            filename_unzipped = legacy_file.filename_unzipped,
            title = legacy_file.songtitle,
            format = self.get_format(legacy_file.format),
            file_size = legacy_file.filesize,
            channels = legacy_file.channels,
            instrument_text = legacy_file.insttext,
            comment_text = legacy_file.comment,
            hash = legacy_file.hash,
            pattern_hash = legacy_file.patternhash,
            license = self.get_license(legacy_file.license),
            create_date = create_date,
            update_date = legacy_file.timestamp,
            genre = self.get_genre(legacy_file.genre_id),
            folder = legacy_file.download
        )

        # Generate song stats
        SongStats.objects.create(
            song = song,
            downloads = legacy_file.hits,
            total_comments = legacy_file.comment_total,
            average_comment_score = legacy_file.comment_score,
            total_reviews = legacy_file.review_total,
            average_review_score = legacy_file.review_score,
        )

    def get_genre(self, genre_id):
        match genre_id:
            case 0:
                return None
            case 1:
                return Song.Genres.ELECTRONIC_GENERAL
            case 2:
                return Song.Genres.ELECTRONIC_AMBIENT
            case 3:
                return Song.Genres.ELECTRONIC_DANCE
            case 58:
                return Song.Genres.POP_DISCO
            case 6:
                return Song.Genres.ELECTRONIC_DRUM_AND_BASS
            case 7:
                return Song.Genres.ELECTRONIC_TECHNO
            case 8:
                return Song.Genres.OTHER_VIDEO_GAME
            case 9:
                return Song.Genres.ELECTRONIC_BREAKBEAT
            case 10:
                return Song.Genres.ELECTRONIC_HOUSE
            case 11:
                return Song.Genres.ELECTRONIC_PROGRESSIVE
            case 12:
                return Song.Genres.POP_GENERAL
            case 13:
                return Song.Genres.POP_ROCK_GENERAL
            case 14:
                return Song.Genres.POP_ROCK_HARD
            case 15:
                return Song.Genres.POP_ROCK_SOFT
            case 18:
                return Song.Genres.OTHER_COUNTRY
            case 19:
                return Song.Genres.JAZZ_BLUES
            case 20:
                return Song.Genres.OTHER_CLASSICAL
            case 21:
                return Song.Genres.OTHER_FOLK
            case 22:
                return Song.Genres.HIP_HOP
            case 23:
                return Song.Genres.OTHER_WORLD_LATIN
            case 24:
                return Song.Genres.SKA
            case 25:
                return Song.Genres.SOUL
            case 26:
                return Song.Genres.R_AND_B
            case 27:
                return Song.Genres.REGGAE
            case 28:
                return Song.Genres.OTHER_MEDIEVAL
            case 29:
                return Song.Genres.JAZZ
            case 30:
                return Song.Genres.JAZZ_ACID
            case 31:
                return Song.Genres.JAZZ_MODERN
            case 32:
                return Song.Genres.POP_FUNK
            case 33:
                return Song.Genres.ALTERNATIVE
            case 34:
                return Song.Genres.ELECTRONIC_INDUSTRIAL
            case 35:
                return Song.Genres.ALTERNATIVE_PUNK
            case 36:
                return Song.Genres.ALTERNATIVE_METAL
            case 37:
                return Song.Genres.ALTERNATIVE_METAL_EXTREME
            case 38:
                return Song.Genres.ALTERNATIVE_GOTHIC
            case 39:
                return Song.Genres.ELECTRONIC_HARDCORE
            case 40:
                return Song.Genres.ELECTRONIC_GABBER
            case 41:
                return Song.Genres.OTHER_OTHER
            case 42:
                return Song.Genres.OTHER_WORLD
            case 43:
                return Song.Genres.OTHER_SOUNDTRACK
            case 44:
                return Song.Genres.OTHER_NEWAGE
            case 45:
                return Song.Genres.OTHER_COMEDY
            case 46:
                return Song.Genres.OTHER_EXPERIMENTAL
            case 47:
                return Song.Genres.OTHER_SPIRITUAL
            case 48:
                return Song.Genres.ALTERNATIVE
            case 49:
                return Song.Genres.OTHER_RELIGIOUS
            case 50:
                return Song.Genres.OTHER_ORCH
            case 52:
                return Song.Genres.OTHER_FANTASY
            case 53:
                return Song.Genres.DEMO_1HRCOMPO
            case 54:
                return Song.Genres.DEMO_CHIPTUNE
            case 55:
                return Song.Genres.DEMO_STYLE
            case 56:
                return Song.Genres.POP_BALLAD
            case 59:
                return Song.Genres.OTHER_PIANO
            case 60:
                return Song.Genres.ELECTRONIC_JUNGLE
            case 61:
                return Song.Genres.POP_SYNTH
            case 62:
                return Song.Genres.POP_SOFT
            case 63:
                return Song.Genres.ELECTRONIC_TRANCE_ACID
            case 64:
                return Song.Genres.ELECTRONIC_TRANCE_HARD
            case 65:
                return Song.Genres.ELECTRONIC_RAVE
            case 66:
                return Song.Genres.ELECTRONIC_TRANCE_GOA
            case 67:
                return Song.Genres.ELECTRONIC_TRANCE_DREAM
            case 68:
                return Song.Genres.POP_EASY_LISTENING
            case 70:
                return Song.Genres.ELECTRONIC_TRANCE_TRIBAL
            case 71:
                return Song.Genres.ELECTRONIC_TRANCE_GENERAL
            case 72:
                return Song.Genres.CHRISTMAS
            case 74:
                return Song.Genres.JAZZ_BIG_BAND
            case 75:
                return Song.Genres.JAZZ_SWING
            case 76:
                return Song.Genres.OTHER_VOX_MONTAGE
            case 85:
                return Song.Genres.ELECTRONIC_TRANCE_PROGRESSIVE
            case 99:
                return Song.Genres.ELECTRONIC_IDM
            case 100:
                return Song.Genres.ELECTRONIC_OTHER
            case 101:
                return Song.Genres.ELECTRONIC_MINIMAL
            case 102:
                return Song.Genres.OTHER_FUSION
            case 103:
                return Song.Genres.ALTERNATIVE_GRUNGE
            case 105:
                return Song.Genres.OTHER_BLUEGRASS
            case  106:
                return Song.Genres.ELECTRONIC_CHILLOUT
            case 107:
                return Song.Genres.POP_EASY_LISTENING

    def get_format(self, format):
        match format:
            case 'it':
                return Song.Formats.IT
            case 's3m':
                return Song.Formats.S3M
            case 'mod':
                return Song.Formats.MOD
            case 'xm':
                return Song.Formats.XM
            case '669':
                return Song.Formats._669
            case 'ahx':
                return Song.Formats.AHX
            case 'amf':
                return Song.Formats.AMF
            case 'ams':
                return Song.Formats.AMS
            case 'c67':
                return Song.Formats.C67
            case 'dbm':
                return Song.Formats.DBM
            case 'digi':
                return Song.Formats.DIGI
            case 'dmf':
                return Song.Formats.DMF
            case 'dsm':
                return Song.Formats.DSM
            case 'dsym':
                return Song.Formats.DSYM
            case 'dtm':
                return Song.Formats.DTM
            case 'far':
                return Song.Formats.FAR
            case 'fmt':
                return Song.Formats.FMT
            case 'gdm':
                return Song.Formats.GDM
            case 'hvl':
                return Song.Formats.HVL
            case 'imf':
                return Song.Formats.IMF
            case 'j2b':
                return Song.Formats.J2B
            case 'mdl':
                return Song.Formats.MDL
            case 'med':
                return Song.Formats.MED
            case 'mo3':
                return Song.Formats.MO3
            case 'mptm':
                return Song.Formats.MPTM
            case 'mt2':
                return Song.Formats.MT2
            case 'mtm':
                return Song.Formats.MTM
            case 'okt':
                return Song.Formats.OKT
            case 'plm':
                return Song.Formats.PLM
            case 'psm':
                return Song.Formats.PSM
            case 'ptm':
                return Song.Formats.PTM
            case 'sfx':
                return Song.Formats.SFX
            case 'stm':
                return Song.Formats.STM
            case 'stp':
                return Song.Formats.STP
            case 'stx':
                return Song.Formats.STX
            case 'symmod':
                return Song.Formats.SymMOD
            case 'ult':
                return Song.Formats.ULT
            case 'umx':
                return Song.Formats.UMX
        return None

    def get_license(self, license):
        match license:
            case 'publicdomain':
                return Song.Licenses.PUBLIC_DOMAIN
            case 'by-nc':
                return Song.Licenses.NON_COMMERCIAL
            case 'by-nc-nd':
                return Song.Licenses.NON_COMMERCIAL_NO_DERIVATIVES
            case 'by-nc-sa':
                return Song.Licenses.NON_COMMERCIAL_SHARE_ALIKE
            case 'by-nd':
                return Song.Licenses.NO_DERIVATIVES
            case 'by-sa':
                return Song.Licenses.SHARE_ALIKE
            case 'by':
                return Song.Licenses.ATTRIBUTION
            case 'cc0':
                return Song.Licenses.CC0
        return ''
