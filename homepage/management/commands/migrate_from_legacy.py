from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.db.models.signals import *
from collections import defaultdict

from homepage import legacy_models
from homepage.models import Profile
from artists.models import Artist
from songs.models import Song, SongStats, ArtistComment, Favorite, Comment, NewSong

class Command(BaseCommand):
    help = "Migrates a legacy database table"

    def add_arguments(self, parser):
        parser.add_argument('source_table', type=str)

    def handle(self, *args, **options):
        source_table = options['source_table']

        if ('users' == source_table):
            with DisableSignals():
                self.migrate_users_table()

        if ('files' == source_table):
            with DisableSignals():
                self.migrate_files_table()

        if ('tma_artist_mappings_real' == source_table):
            with DisableSignals():
                self.migrate_real_artist_mappings_table()

        if ('tma_favourites' == source_table):
            with DisableSignals():
                self.migrate_favorites()

        if ('tma_comments' == source_table):
            with DisableSignals():
                self.migrate_comments()

        if ('files_new' == source_table):
            self.migrate_files_new()

        if ('tma_nominations' == source_table):
            self.migrate_nominations()
    
    def migrate_comments(self):
        comments = legacy_models.TmaComments.objects.using('legacy').all()
        total = len(comments)
        counter = 0
        print(f"Starting migration of {total} comments. This process will add comments and ratings to songs.")

        for comment in comments:
            counter += 1

            if (counter % 1000 == 0):
                print(f"Generated {counter} out of {total} comments.")

            # Get the profile
            try:
                profile = Profile.objects.get(legacy_id=comment.userid) if comment.userid != 1 else None
            except ObjectDoesNotExist:
                print(f"Could not find a profile for record with id {comment.id} and userid {comment.userid}")
                continue

            # Get the song
            try:
                song = Song.objects.get(legacy_id=comment.moduleid)
            except ObjectDoesNotExist:
                print(f"Could not find a song for record with id {comment.id} and song id {comment.moduleid}")
                continue

            # Save the record - remember that anonymous comments are allowed
            try:
                Comment.objects.create(
                    profile=profile,
                    song=song,
                    text=comment.comment_text,
                    rating=comment.comment_rating,
                    create_date=comment.comment_date
                )
            except IntegrityError:
                print(f"Integrity error when trying to create a favorite for record {comment.id}, profile {profile.pk} ({profile.display_name}) and song {song.pk} ({song.get_title})")

    def migrate_favorites(self):
        favorites = legacy_models.TmaFavourites.objects.using('legacy').all()

        total = len(favorites)
        counter = 0
        print(f"Starting migration of {total} favorites. This process will associate profiles with favorite songs.")

        for fave in favorites:
            counter += 1
            if (counter % 1000 == 0):
                print(f"Generated {counter} out of {total} favorites.")

            # Get the profile
            try:
                profile = Profile.objects.get(legacy_id=fave.userid)
            except ObjectDoesNotExist:
                print(f"Could not find a profile for record with id {fave.id} and userid {fave.userid}")
                continue

            # Get the song
            try:
                song = Song.objects.get(legacy_id=fave.moduleid)
            except ObjectDoesNotExist:
                print(f"Could not find a song for record with id {fave.id} and song id {fave.moduleid}")
                continue

            # Save the record
            try:
                Favorite.objects.create(profile=profile, song=song)
            except IntegrityError:
                print(f"Integrity error when trying to create a favorite for record {fave.id}, profile {profile.pk} ({profile.display_name}) and song {song.pk} ({song.get_title})")
                continue

    def migrate_real_artist_mappings_table(self):
        mappings = legacy_models.TmaArtistMappingsReal.objects.using('legacy').all()
        
        total = len(mappings)
        counter = 0
        comment_counter = 0
        print(f"Starting migrations of {total} song-artist mappings. This process will associate songs with artists and add artist comments, when found.")
        for mapping in mappings:
            counter += 1
            if (mapping.description):
                comment_counter += 1
                if (comment_counter % 1000 == 0):
                    print(f"Generated {comment_counter} artist comments")
            
            if (counter % 1000 == 0):
                print(f"Generated {counter} out of {total} mappings.")
            
            # Get the correct artist
            try:
                artist = Artist.objects.get(legacy_id=mapping.artist)
            except ObjectDoesNotExist:
                print(f"Artist does not exist for legacy id {mapping.artist}")
            
            # Get the song by hash and/or filename
            try:
                song = Song.objects.get(filename=mapping.filename, hash=mapping.hash)
            except ObjectDoesNotExist:
                print(f"Song does not exist for {mapping.filename}")
            except MultipleObjectsReturned:
                print(f"Multiple songs returned for {mapping.filename}")

            # Associate the song with the artist
            if artist and song:
                artist.songs.add(song)
                artist.save()

                if artist.profile.pk == 4104 and song.id == 138010:
                    print(f"Found an instance of that song! pk in mapping table is {mapping.pk}")

                if (mapping.description):
                    try:
                        ArtistComment.objects.create(
                            profile = artist.profile,
                            song = song,
                            text = mapping.description
                        )
                    except IntegrityError:
                        print(f"Integrity error on when saving artist comment for record {mapping.pk} for profile {artist.profile.id} ({artist.profile.display_name}) and song {song.id} ({song.title})")

    def migrate_files_table(self):
        files = legacy_models.Files.objects.using('legacy').all().order_by('id')

        total = len(files)
        counter = 0
        print(f"Starting migrations of {total} files. This process will create all song and song_stats objects.")
        
        for file in files:
            counter += 1

            if (counter % 1000 == 0):
                print(f"Generated {counter} out of {total} from the legacy files table.")

            self.generate_song(file)

    def generate_song(self, legacy_file):
        # Generate song
        create_date = legacy_file.date if legacy_file.date else legacy_file.timestamp
        
        song = Song.objects.create(
            legacy_id = legacy_file.id, 
            filename = legacy_file.filename,
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
            genre = self.get_genre(legacy_file.genre_id)
        )

        # Generate song stats
        stats = SongStats.objects.create(
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

    def migrate_users_table(self):
        users = legacy_models.Users.objects.using('legacy').all().order_by('userid')
        total = len(users)

        print(f"Starting migrations of {total} users. This process will create all user, profile, and artist objects.")
        counter = 0

        for user in users:
            counter += 1
            if (counter % 1000 == 0):
                print(f"Generated {counter} out of {total} from the legacy users table.")
            new_user = self.generate_user(user)

            if not new_user:
                continue

            new_profile = self.generate_profile(user, new_user)

            if not new_profile or not user.cred_artist:
                continue

            new_artist = self.generate_artist(user, new_user, new_profile)
    
    def migrate_files_new(self):
        files = legacy_models.FilesNew.objects.using('legacy').all().order_by('id')

        total = len(files)
        counter = 0
        print(f"Starting migrations of {total} files from files_new.")

        for file in files:
            counter += 1

            if (counter % 1000 == 0):
                print(f"Generated {counter} out of {total} from the legacy files_new table.")

            # Get the profile
            try:
                profile = Profile.objects.get(legacy_id=file.uploader_uid) if file.uploader_uid != 1 else None
            except ObjectDoesNotExist:
                print(f"Could not find a profile for user_id {file.uploader_uid} for record from files_new with id {file.id}")
                continue

            NewSong.objects.create(
                filename=file.filename,
                title=file.songtitle,
                format=file.filename.split('.')[-1],
                file_size=file.filesize,
                channels=file.channels,
                instrument_text=file.insttext,
                comment_text=file.comment,
                hash=file.hash,
                pattern_hash=file.patternhash,
                artist_from_file=file.artist_file,
                uploader_profile=profile,
                uploader_ip_address=file.uploader,
                is_by_uploader=file.ismine,
                create_date=file.dateuploaded
            )

    def migrate_nominations(self):
        nominations = legacy_models.TmaNominations.objects.using('legacy').all().order_by('id')
        
        total = len(nominations)
        counter = 0
        print(f"Starting migrations of {total} records from tma_nominations.")

        for nom in nominations:
            counter += 1

            if (counter % 1000 == 0):
                print(f"Updated {counter} out of {total} songs with nomination info.")

            # Get the record from the songs table
            try:
                song = Song.objects.get(hash=nom.hash)
            except ObjectDoesNotExist:
                print(f"Song does not exist for hash {nom.hash}")
                continue
            except MultipleObjectsReturned:
                print(f"Multiple songs returned for hash {nom.hash}")
                continue

            # Get the profile
            try:
                profile = Profile.objects.get(legacy_id=nom.userid) if nom.userid != 1 else None
            except ObjectDoesNotExist:
                profile = None

            song.is_featured = True
            song.featured_date = nom.date
            song.featured_by = profile
            song.save()

    def generate_user(self, legacy_user):
        username = legacy_user.username
        password = self.get_password_with_hashing_algorithm(legacy_user.profile_password)
        email = legacy_user.profile_email
        is_staff = True if legacy_user.cred_admin else False
        date_joined = legacy_user.date

        try:
            return User.objects.create(username = username, password = password, email = email, date_joined = date_joined, is_staff = is_staff)
        except IntegrityError as e:
            print(f"Could not create user {username} due to IntegrityError {str(e)}")
            return None

    def generate_profile(self, legacy_user, new_user):
        try:
            return Profile.objects.create(
                user = new_user,
                display_name = legacy_user.profile_fullname,
                blurb = legacy_user.profile_blurb,
                create_date = legacy_user.date,
                update_date = legacy_user.lastlogin,
                legacy_id = legacy_user.userid
            )
        except IntegrityError as e:
            print(f"Could not create profile for user {new_user.username} due to IntegrityError {str(e)}")
            return None

    def generate_artist(self, legacy_user, new_user, profile):
        try:
            return Artist.objects.create(
                user = new_user,
                profile = profile,
                legacy_id = legacy_user.userid,
                name = legacy_user.profile_fullname,
                create_date = legacy_user.date,
                update_date = legacy_user.lastlogin
            )
        except IntegrityError as e:
            print(f"Could not create artist for user {new_user.username} due to IntegrityError {str(e)}")
            print(f"Trying again with username {legacy_user.profile_fullname}_1 instead")

            return Artist.objects.create(
                user = new_user,
                profile = profile,
                legacy_id = legacy_user.userid,
                name = legacy_user.profile_fullname + "_1",
                create_date = legacy_user.date,
                update_date = legacy_user.lastlogin
            )

    def get_password_with_hashing_algorithm(self, password):
        if password.startswith("$2y"):
            return "bcrypt$" + password
        
        if password:
            return "hmac$" + password

        return password

class DisableSignals(object):
    def __init__(self, disabled_signals=None):
        self.stashed_signals = defaultdict(list)
        self.disabled_signals = disabled_signals or [
            pre_init, post_init,
            pre_save, post_save,
            pre_delete, post_delete,
            pre_migrate, post_migrate,
        ]

    def __enter__(self):
        for signal in self.disabled_signals:
            self.disconnect(signal)

    def __exit__(self, exc_type, exc_val, exc_tb):
        for signal in list(self.stashed_signals):
            self.reconnect(signal)

    def disconnect(self, signal):
        self.stashed_signals[signal] = signal.receivers
        signal.receivers = []

    def reconnect(self, signal):
        signal.receivers = self.stashed_signals.get(signal, [])
        del self.stashed_signals[signal]