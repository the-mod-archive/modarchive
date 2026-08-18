from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete

from interactions.models import Comment
from songs.models import Song

@receiver(post_save, sender=Comment)
def update_song_stats_after_save(_sender=None, instance=None, **kwargs):
    update_song_stats(instance.song)

@receiver(post_delete, sender=Comment)
def update_song_stats_after_delete(_sender=None, instance=None, **kwargs):
    update_song_stats(instance.song)

def update_song_stats(song):
    if not Song.objects.filter(pk=song.pk).exists():
        return

    total_comments = song.comment_set.all().count()
    song.comments_count = total_comments
    song.average_rating = get_average_rating(song, total_comments)
    song.cumulative_rating = song.comments_count * (song.average_rating or 0)
    song.save()

def get_average_rating(song, total_comments):
    if total_comments == 0:
        return None

    return sum(comment.rating for comment in song.comment_set.all()) / total_comments

def get_cumulative_rating(song, total_comments):
    if total_comments == 0:
        return None
    return sum(comment.rating for comment in song.comment_set.all())
