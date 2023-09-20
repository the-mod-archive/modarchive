from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

from homepage import legacy_models
from homepage.models import Profile
from songs.models import Song

class Command(BaseCommand):
    help = "Migrate the legacy nominations table"

    def handle(self, *args, **options):
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