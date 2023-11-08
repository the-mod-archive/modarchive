from rest_framework import serializers
from songs.models import Song, SongStats
from artists.models import Artist

class ArtistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Artist
        fields = [
            'id',
            'name'
        ]

class SongStatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SongStats
        fields = [
            'downloads',
            'total_comments',
            'average_comment_score',
            'total_favorites'
        ]

class SongSerializer(serializers.ModelSerializer):
    stats = SongStatsSerializer(source='get_stats', read_only=True)
    artists = ArtistSerializer(many=True, read_only=True, source='artist_set')

    class Meta:
        model = Song
        fields = [
            'id',
            'title',
            'clean_title',
            'filename',
            'file_size',
            'channels',
            'format',
            'instrument_text',
            'comment_text',
            'license',
            'genre',
            'stats',
            'artists'
        ]