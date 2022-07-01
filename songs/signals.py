from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete

from songs.models import Comment

@receiver(post_save, sender=Comment)
def update_song_stats_after_save(sender, instance, **kwargs):
    update_song_stats(instance.song)

@receiver(post_delete, sender=Comment)
def update_song_stats_after_delete(sender, instance, **kwargs):
    update_song_stats(instance.song)

def update_song_stats(song):
    total_comments = song.comment_set.all().count()

    song.songstats.total_comments = total_comments
    song.songstats.average_comment_score = get_average_rating(song, total_comments)
    song.songstats.save()

def get_average_rating(song, total_comments):
    if (total_comments == 0):
        return 0.0

    return sum(comment.rating for comment in song.comment_set.all()) / total_comments