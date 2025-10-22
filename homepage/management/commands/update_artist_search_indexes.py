from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.postgres.search import SearchVector
import operator
from functools import reduce

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
        # Determine which artists to update
        if options['artist_id']:
            # Single artist update
            artist_queryset = Artist.objects.filter(id=options['artist_id'])
        elif options['start_id'] and options['end_id']:
            # Range update
            artist_queryset = Artist.objects.filter(id__gte=options['start_id'], id__lte=options['end_id'])
        elif options['all']:
            # All artists
            artist_queryset = Artist.objects.all()
        else:
            self.stdout.write('No artists found to update')
            return

        total = artist_queryset.count()
        if total == 0:
            self.stdout.write('No artists found to update')
            return

        self.stdout.write(f'Updating search vectors for {total} artists...')

        # Process in batches for better performance and memory efficiency
        batch_size = 1000
        counter = 0
        successful_updates = 0
        failed_updates = 0

        # Use iterator to avoid loading all records into memory
        for artist_batch in self.chunked_iterator(artist_queryset, batch_size):
            # Batch update search vectors
            updated_count = self.bulk_update_search_vectors(artist_batch)
            successful_updates += updated_count
            counter += len(artist_batch)
            
            if counter % 5000 == 0 or counter == total:
                self.stdout.write(f"Updated search vectors for {counter} out of {total} artists. "
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

    def bulk_update_search_vectors(self, artist_batch):
        """Update search vectors for a batch of artists using a single query"""
        try:
            with transaction.atomic():
                # Get the IDs of artists in this batch
                artist_ids = [artist.id for artist in artist_batch]
                
                # Bulk update search vectors using a single query
                # This replicates what the signal does but in bulk
                search_vector = reduce(operator.add, [SearchVector('name')])
                
                updated_count = Artist.objects.filter(id__in=artist_ids).update(
                    search_document=search_vector
                )
                
                return updated_count
                
        except Exception as e:
            self.stderr.write(f'Error updating search vectors for batch: {str(e)}')
            
            # Fall back to individual updates for this batch
            successful_individual = 0
            for artist in artist_batch:
                try:
                    signals.index_artist(sender=Artist, instance=artist)
                    successful_individual += 1
                except Exception as individual_error:
                    self.stderr.write(f'Failed to update search vector for artist {artist.id}: {individual_error}')
            
            return successful_individual
