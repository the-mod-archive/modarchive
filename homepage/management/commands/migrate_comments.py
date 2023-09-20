from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.db.models import F

from .disable_signals import DisableSignals
from homepage import legacy_models
from homepage.models import Profile
from songs.models import Song, Comment

class Command(BaseCommand):
    help = "Migrate the legacy comments table"

    def handle(self, *args, **options):
        with DisableSignals():
            comments = legacy_models.TmaComments.objects.using('legacy').all()
            total = len(comments)
            counter = 0
            print(f"Starting migration of {total} comments. This process will add comments and ratings to songs.")

            for comment in comments:
                counter += 1

                if (counter % 1000 == 0):
                    print(f"Generated {counter} out of {total} comments.")

                # Get the profile
                try:
                    profile = Profile.objects.get(legacy_id=comment.userid) if comment.userid != 1 else None
                except ObjectDoesNotExist:
                    print(f"Could not find a profile for record with id {comment.id} and userid {comment.userid}")
                    continue

                # Get the song
                try:
                    song = Song.objects.get(legacy_id=comment.moduleid)
                except ObjectDoesNotExist:
                    print(f"Could not find a song for record with id {comment.id} and song id {comment.moduleid}")
                    continue

                # Save the record - remember that anonymous comments are allowed
                try:
                    Comment.objects.create(
                        profile=profile,
                        song=song,
                        text=comment.comment_text,
                        rating=comment.comment_rating,
                        create_date=comment.comment_date
                    )
                except IntegrityError:
                    print(f"Integrity error when trying to create a favorite for record {comment.id}, profile {profile.pk} ({profile.display_name}) and song {song.pk} ({song.get_title})")