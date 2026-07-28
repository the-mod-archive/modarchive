import logging
from django.db.models import Sum, Avg
from artists.models import Artist

logger = logging.getLogger(__name__)

def daily_heartbeat():
    logger.info("Daily scheduled job ran successfully.")

def update_artist_stats():
    """
    Update stats for all artists:
    - total_songs: Count of all songs by the artist
    - total_downloads: Sum of downloads from all songs by the artist
    - total_comments: Sum of comments on all songs by the artist
    - average_song_rating: Average of ratings from all songs by the artist
    - cumulative_song_ratings: Cumulative ratings from all songs by the artist
    """
    artists = Artist.objects.all()
    updated_count = 0

    for artist in artists:
        # Get all songs for this artist
        songs = artist.songs.all()

        # Calculate total songs
        total_songs = songs.count()

        # Calculate total downloads
        total_downloads_result = songs.aggregate(total=Sum('downloads_count'))
        total_downloads = total_downloads_result['total'] or 0

        # Calculate total comments
        total_comments_result = songs.aggregate(total=Sum('comments_count'))
        total_comments = total_comments_result['total'] or 0

        # Calculate average rating
        average_rating_result = songs.aggregate(avg=Avg('average_rating'))
        average_rating = average_rating_result['avg'] or 0

        # Calculate cumulative song ratings
        total_ratings_result = songs.aggregate(total=Sum('cumulative_rating'))
        cumulative_song_ratings = total_ratings_result['total'] or 0

        # Update the artist
        artist.total_songs = total_songs
        artist.total_downloads = total_downloads
        artist.total_comments = total_comments
        artist.cumulative_song_ratings = cumulative_song_ratings
        artist.average_song_rating = average_rating
        artist.save()

        updated_count += 1

    logger.info(f"Updated stats for {updated_count} artists.")
