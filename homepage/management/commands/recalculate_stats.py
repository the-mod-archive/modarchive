from django.core.management.base import BaseCommand
from django.db.models import Count, Avg, Sum

from songs.models import Song


BATCH_SIZE = 1000

def _bulk_save(batch):
    Song.objects.bulk_update(batch, ['comments_count', 'favorites_count', 'average_rating', 'cumulative_rating'])

class Command(BaseCommand):
    help = 'Recalculate the average rating and counts of favorites and comments for each song and update the song records.'

    def add_arguments(self, parser):
        parser.add_argument('--song_id', type=int, help='Limit the calculation to a single song ID.')

    def handle(self, *args, **options):
        song_id = options.get('song_id')

        songs = Song.objects.all()

        if song_id:
            songs = songs.filter(id=song_id)

        # Annotate everything in ONE query
        songs = songs.annotate(
            total_favorites=Count('favorite', distinct=True),
            total_comments=Count('comment', distinct=True),
            average_comment_score=Avg('comment__rating'),
        )

        total = songs.count()
        print(f"Starting to recalculate stats for {total} songs.")

        batch = []
        counter = 0

        for song in songs.iterator(chunk_size=BATCH_SIZE):
            # Update the song model fields
            song.comments_count = song.total_comments
            song.favorites_count = song.total_favorites
            song.average_rating = song.average_comment_score
            song.cumulative_rating = song.comments_count * (song.average_rating or 0.0)

            batch.append(song)

            counter += 1

            if len(batch) >= BATCH_SIZE:
                _bulk_save(batch)
                print(f"Recalculated stats for {counter} songs.")
                batch = []

        # Save remaining
        if batch:
            _bulk_save(batch)

        self.stdout.write(self.style.SUCCESS('Successfully recalculated song stats.'))

