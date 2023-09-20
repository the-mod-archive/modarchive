from django.core.management.base import BaseCommand
from django.db import IntegrityError
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

from .disable_signals import DisableSignals
from artists.models import Artist
from homepage import legacy_models
from songs.models import Song, ArtistComment

class Command(BaseCommand):
    help = "Migrate the legacy real artist mappings table"

    def handle(self, *args, **options):
        with DisableSignals():
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

                if (mapping.description):
                    try:
                        ArtistComment.objects.create(
                            profile = artist.profile,
                            song = song,
                            text = mapping.description
                        )
                    except IntegrityError:
                        print(f"Integrity error on when saving artist comment for record {mapping.pk} for profile {artist.profile.id} ({artist.profile.display_name}) and song {song.id} ({song.title})")