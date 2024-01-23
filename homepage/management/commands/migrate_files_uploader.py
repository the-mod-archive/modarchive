from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist

from homepage import legacy_models
from homepage.models import Profile
from songs.models import Song
from .disable_signals import DisableSignals

class Command(BaseCommand):
    help = "Migrate the legacy files_uploader table"

    def handle(self, *args, **options):
        with DisableSignals():
            files_uploader = legacy_models.TmaFilesUploader.objects.using('legacy').all()
            total = len(files_uploader)
            counter = 0
            print(f"Starting migration of {total} files_uploader. This process will add uploader profiles to songs.")

            for file_uploader in files_uploader:
                counter += 1

                if counter % 1000 == 0:
                    print(f"Generated {counter} out of {total} files_uploader.")

                try:
                    profile = Profile.objects.get(legacy_id=file_uploader.userid) if file_uploader.userid != 1 else None
                except ObjectDoesNotExist:
                    print(f"Could not find a profile for record with userid {file_uploader.userid} and song id {file_uploader.moduleid}")
                    continue

                try:
                    song = Song.objects.get(legacy_id=file_uploader.moduleid)
                except ObjectDoesNotExist:
                    print(f"Could not find a song for record with userid {file_uploader.userid} and song id {file_uploader.moduleid}")
                    continue

                song.uploaded_by = profile
                song.save()
