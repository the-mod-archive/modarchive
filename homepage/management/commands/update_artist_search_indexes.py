from django.core.management.base import BaseCommand

from search import signals
from artists.models import Artist

class Command(BaseCommand):
    help = 'Updates the search index for an artist'

    def add_arguments(self, parser):
        parser.add_argument('artist_id', nargs='?', type=int,
                            help='The ID of the artist to rebuild search index')
        parser.add_argument('--start_id', type=int,
                            help='The ID of the first artist to rebuild search index')
        parser.add_argument('--end_id', type=int,
                            help='The ID of the last artist to rebuild search index')
        parser.add_argument('--all', action='store_true',
                            help='Update the search vector fields for all artists')
        
    def handle(self, *args, **options):
        artist_ids = set()

        if options['artist_id']:
            artist_ids.add(options['artist_id'])
        elif options['start_id'] and options['end_id']:
            artist_ids = set(range(options['start_id'], options['end_id'] + 1))
        elif options['all']:
            artist_ids = set(Artist.objects.values_list('id', flat=True))

        if not artist_ids:
            self.stdout.write('No artists found to update')
            return
        
        self.stdout.write(f'Updating {len(artist_ids)} artists...')

        for artist_id in artist_ids:
            try:
                artist = Artist.objects.get(id=artist_id)
                signals.index_artist(sender=Artist, instance=artist)
                self.stdout.write(f'Search vector fields updated for artist {artist_id}')
            except Artist.DoesNotExist:
                self.stderr.write(f'Artist with ID {artist_id} does not exist')
                continue