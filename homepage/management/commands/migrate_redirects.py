from django.core.management.base import BaseCommand
from django.core.exceptions import ValidationError

from homepage import legacy_models
from songs.models import Song, SongRedirect

class Command(BaseCommand):
    help = "Migrate the legacy tma_redirects table"

    def handle(self, *args, **options):
        redirects = legacy_models.TmaRedirects.objects.using('legacy').all()
        total = len(redirects)

        print(f"Starting migration of {total} records from tma_redirects. This process will populate the song redirects table.")

        for redirect in redirects:
            try:
                song = Song.objects.get(id=redirect.redirect_to)
                if song:
                    SongRedirect.objects.create(
                        song=song,
                        old_song_id=redirect.redirect_from
                    )
            except Song.DoesNotExist:
                print(f"Could not find song with legacy_id {redirect.redirect_to} for redirect {redirect.redirect_from}")
            except ValidationError:
                print(f"Validation error, redirect_from value is {redirect.redirect_from}")
