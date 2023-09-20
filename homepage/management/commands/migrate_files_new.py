from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist

from .disable_signals import DisableSignals
from homepage import legacy_models
from homepage.models import Profile
from songs.models import NewSong

class Command(BaseCommand):
    help = "Migrate the legacy files_new table"

    def handle(self, *args, **options):
        with DisableSignals():
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