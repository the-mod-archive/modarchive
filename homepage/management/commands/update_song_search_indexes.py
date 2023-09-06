from django.core.management.base import BaseCommand

from search import signals
from songs.models import Song

class Command(BaseCommand):
    help = 'Updates the search index for a song'

    def add_arguments(self, parser):
        parser.add_argument('song_id', nargs='?', type=int,
                            help='The ID of the song to update')
        parser.add_argument('--start_id', type=int,
                            help='The ID of the first song to update')
        parser.add_argument('--end_id', type=int,
                            help='The ID of the last song to update')
        parser.add_argument('--all', action='store_true',
                            help='Update the search vector fields for all songs')

    def handle(self, *args, **options):
        song_ids = set()

        if options['song_id']:
            song_ids.add(options['song_id'])
        elif options['start_id'] and options['end_id']:
            song_ids = set(range(options['start_id'], options['end_id'] + 1))
        elif options['all']:
            song_ids = set(Song.objects.values_list('id', flat=True))

        if not song_ids:
            self.stdout.write('No songs found to update')
            return
        
        self.stdout.write(f'Updating {len(song_ids)} songs...')
        counter = 0

        for song_id in song_ids:
            try:
                counter += 1
                if (counter % 1000 == 0):
                    print(f"Updated search vectors for {counter} out of {len(song_ids)} songs.")

                song = Song.objects.get(id=song_id)
                signals.index_song(sender=Song, instance=song)
            except Song.DoesNotExist:
                self.stderr.write(f'Song with ID {song_id} does not exist')
                continue