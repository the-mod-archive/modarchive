from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.db.models import F

from homepage import legacy_models
from homepage.models import Profile
from interactions.models import Favorite
from songs.models import Song
from .disable_signals import DisableSignals

class Command(BaseCommand):
    help = "Migrate the legacy favorites table"

    def handle(self, *args, **options):
        with DisableSignals():
            favorites = legacy_models.TmaFavourites.objects.using('legacy').all()

            total = len(favorites)
            counter = 0
            print(f"Starting migration of {total} favorites. This process will associate profiles with favorite songs.")

            for fave in favorites:
                counter += 1
                if counter % 1000 == 0:
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

                # Increment the number of favorites
                try:
                    stats = song.get_stats()
                    stats.total_favorites = F('total_favorites') + 1
                    stats.save()
                except IntegrityError:
                    print(f"Integrity error when trying to increment favorites count for record {fave.id}, profile {profile.pk} ({profile.display_name}) and song {song.pk} ({song.get_title})")
