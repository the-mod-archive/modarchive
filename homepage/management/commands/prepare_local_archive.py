from django.conf import settings
from django.core.management.base import BaseCommand
import logging
from pathlib import Path
import re
import requests
import sys

from songs.models import Song

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Sets up the local environment environment for serving files'

    def add_arguments(self, parser):
        parser.add_argument('song_id', nargs='?', type=int,
                            help='The ID of the song to retrieve')

    def handle(self, *args, **options):
        if settings.SETTINGS_MODULE != 'modarchive.settings.dev':
            print("This command can only be run with the dev settings module.")
            sys.exit(1)

        main_dir = Path(settings.MAIN_ARCHIVE_DIR)
        base_url: str = settings.SONG_SOURCE
        main_dir.mkdir(parents=True, exist_ok=True)

        if options['song_id']:
            song = Song.objects.get(id=options['song_id'])
            self.get_song(song, main_dir, base_url)
        else:
            songs = Song.objects.all()[:50]
            for song in songs:
                self.get_song(song, main_dir, base_url)
    
    def get_song(self, song: Song, main_dir: Path, base_url: str):
        # Validate format before using in path
        valid_formats = {choice[0].upper() for choice in Song.Formats.choices}
        format_name = song.format.upper()
        if format_name not in valid_formats:
            print(f"Invalid format '{song.format}' for song '{song.title}'. Skipping.")
            return
        format_dir = main_dir / format_name
        if not format_dir.exists():
            print(f"Creating format directory: {format_dir}")
            format_dir.mkdir()
        
        # Validate that song.folder is a single uppercase letter or '0_9'
        if not re.match(r"^[A-Z]$|^[0-1]_9$", str(song.folder)):
            logger.error(f"Invalid folder name '{song.folder}' for song ID {song.id}. Skipping.")
            return

        song_folder = format_dir / song.folder
        if not song_folder.exists():
            print(f"Creating song folder: {song_folder}")
            song_folder.mkdir()
        
        archive_location = Path(song.get_archive_path())
        if archive_location.exists():
            print(f"File already exists for {song.title}")
            return

        url = f"{base_url}?moduleid={song.legacy_id}&zip=1"
        try:
            print(f"⬇️ Downloading {url}")
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            with open(archive_location, 'wb') as f:
                f.write(response.content)

            print(f"✅ Saved {archive_location}")
        except Exception as e:
            print(f"Failed to download song {song.legacy_id}: {e}")
