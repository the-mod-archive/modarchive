from rest_framework import serializers
from songs.models import Song, SongStats
from artists.models import Artist

class LimitedArtistSerializer(serializers.ModelSerializer):
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
    artists = LimitedArtistSerializer(many=True, read_only=True, source='artist_set')

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

class LimitedSongSerializer(serializers.ModelSerializer):
    stats = SongStatsSerializer(source='get_stats', read_only=True)
    
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
            'license',
            'genre',
            'stats',
        ]

class ArtistSerializer(serializers.ModelSerializer):
    songs = LimitedSongSerializer(many=True, read_only=True)
    class Meta:
        model = Artist
        fields = [
            'id',
            'name',
            'songs'
        ]

class SongSearchResultSerializer(serializers.ModelSerializer):
    artists = LimitedArtistSerializer(many=True, read_only=True, source='artist_set')
    
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
            'license',
            'genre',
            'artists'
        ]