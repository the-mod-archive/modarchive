from django.core.management.base import BaseCommand

from interactions.models import Favorite
from songs.models import Song

class Command(BaseCommand):
    help = 'Recalculate the total number of favorites for each song and update SongStats.'

    def add_arguments(self, parser):
        parser.add_argument('--song_id', type=int, help='Limit the calculation to a single song ID.')

    def handle(self, *args, **options):
        song_id = options.get('song_id')

        songs = Song.objects.all()
        if song_id:
            songs = songs.filter(id=song_id)

        for song in songs:
            total_favorites = Favorite.objects.filter(song=song).count()
            song_stats = song.songstats
            song_stats.total_favorites = total_favorites
            song_stats.save()

        self.stdout.write(self.style.SUCCESS('Successfully recalculated song stats.'))
