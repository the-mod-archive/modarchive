from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.postgres.search import SearchVector
import operator
from functools import reduce

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
        # Determine which songs to update
        if options['song_id']:
            # Single song update
            song_queryset = Song.objects.filter(id=options['song_id'])
        elif options['start_id'] and options['end_id']:
            # Range update
            song_queryset = Song.objects.filter(id__gte=options['start_id'], id__lte=options['end_id'])
        elif options['all']:
            # All songs
            song_queryset = Song.objects.all()
        else:
            self.stdout.write('No songs found to update')
            return

        total = song_queryset.count()
        if total == 0:
            self.stdout.write('No songs found to update')
            return
        
        self.stdout.write(f'Updating search vectors for {total} songs...')

        # Process in batches for better performance and memory efficiency
        batch_size = 1000
        counter = 0
        successful_updates = 0
        failed_updates = 0

        # Use iterator to avoid loading all records into memory
        for song_batch in self.chunked_iterator(song_queryset, batch_size):
            # Batch update search vectors
            updated_count = self.bulk_update_search_vectors(song_batch)
            successful_updates += updated_count
            counter += len(song_batch)
            
            if counter % 5000 == 0 or counter == total:
                self.stdout.write(f"Updated search vectors for {counter} out of {total} songs. "
                                f"Successful: {successful_updates}, Failed: {failed_updates}")

        self.stdout.write(f'Search vector update complete!')
        self.stdout.write(f'  Total processed: {counter}')
        self.stdout.write(f'  Successful updates: {successful_updates}')
        self.stdout.write(f'  Failed updates: {failed_updates}')
        
        if counter > 0:
            success_rate = (successful_updates / counter) * 100
            self.stdout.write(f'  Success rate: {success_rate:.1f}%')

    def chunked_iterator(self, queryset, chunk_size):
        """Iterator that yields chunks of objects from a queryset"""
        iterator = queryset.iterator(chunk_size=chunk_size)
        
        chunk = []
        for item in iterator:
            chunk.append(item)
            if len(chunk) >= chunk_size:
                yield chunk
                chunk = []
        
        # Yield remaining items
        if chunk:
            yield chunk

    def bulk_update_search_vectors(self, song_batch):
        """Update search vectors for a batch of songs using a single query"""
        try:
            with transaction.atomic():
                # Get the IDs of songs in this batch
                song_ids = [song.id for song in song_batch]
                
                # Bulk update search vectors using a single query
                # This replicates what the signal does but in bulk
                title_vector = reduce(operator.add, [SearchVector('title')])
                instrument_text_vector = reduce(operator.add, [SearchVector('instrument_text')])
                comment_text_vector = reduce(operator.add, [SearchVector('comment_text')])
                
                updated_count = Song.objects.filter(id__in=song_ids).update(
                    title_vector=title_vector,
                    instrument_text_vector=instrument_text_vector,
                    comment_text_vector=comment_text_vector
                )
                
                return updated_count
                
        except Exception as e:
            self.stderr.write(f'Error updating search vectors for batch: {str(e)}')
            
            # Fall back to individual updates for this batch
            successful_individual = 0
            for song in song_batch:
                try:
                    signals.index_song(sender=Song, instance=song)
                    successful_individual += 1
                except Exception as individual_error:
                    self.stderr.write(f'Failed to update search vector for song {song.id}: {individual_error}')
            
            return successful_individual