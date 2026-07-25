from rest_framework import serializers
from songs.models import Song
from artists.models import Artist

class LimitedArtistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Artist
        fields = [
            'id',
            'name'
        ]

class SongDetailSerializer(serializers.ModelSerializer):
    artists = LimitedArtistSerializer(many=True, read_only=True, source='artist_set')
    
    class Meta:
        model = Song
        fields = [
            'id',
            'title',
            'title_from_file',
            'filename',
            'file_size',
            'channels',
            'format',
            'instrument_text',
            'comment_text',
            'license',
            'genre',
            'downloads_count',
            'comments_count',
            'favorites_count',
            'average_rating',
            'is_featured',
            'artists'
        ]

class SongListSerializer(serializers.ModelSerializer):
    artists = LimitedArtistSerializer(many=True, read_only=True, source='artist_set')
    
    class Meta:
        model = Song
        fields = [
            'id',
            'title',
            'title_from_file',
            'filename',
            'file_size',
            'channels',
            'format',
            'license',
            'genre',
            'downloads_count',
            'comments_count',
            'favorites_count',
            'average_rating',
            'is_featured',
            'artists'
        ]