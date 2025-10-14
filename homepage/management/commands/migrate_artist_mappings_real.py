from django.core.management.base import BaseCommand
from django.db import IntegrityError, transaction
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from collections import defaultdict

from artists.models import Artist
from homepage import legacy_models
from interactions.models import ArtistComment
from songs.models import Song
from .disable_signals import DisableSignals

class Command(BaseCommand):
    help = "Migrate the legacy real artist mappings table"

    def handle(self, *args, **options):
        with DisableSignals():
            # Use iterator() to avoid loading all records into memory
            mappings_queryset = legacy_models.TmaArtistMappingsReal.objects.using('legacy').all()
            total = mappings_queryset.count()
            
            print(f"Starting migrations of {total} song-artist mappings.")
            print("Building lookup dictionaries...")
            
            # Pre-build lookup dictionaries for efficient access
            song_hash_lookup = self.build_song_hash_lookup()
            artist_id_lookup = self.build_artist_id_lookup()
            
            print(f"Built lookup dictionaries: {len(song_hash_lookup)} songs, {len(artist_id_lookup)} artists")
            
            batch_size = 1000
            artist_comments_to_create = []
            artist_song_associations = defaultdict(set)  # artist_id -> set of song_ids
            
            counter = 0
            comment_counter = 0
            skipped_no_artist = 0
            skipped_no_song = 0
            skipped_no_profile = 0
            successful_associations = 0
            
            print("Processing mappings...")
            
            # Process in batches for better performance
            for mapping in mappings_queryset.iterator(chunk_size=batch_size):
                counter += 1
                
                # Look up artist using pre-built dictionary
                # Handle missing artist ID gracefully (no referential integrity in legacy DB)
                artist = artist_id_lookup.get(mapping.artist) if mapping.artist else None
                if not artist:
                    skipped_no_artist += 1
                    if skipped_no_artist <= 10:  # Only show first 10 warnings
                        print(f"Artist does not exist for legacy id {mapping.artist} (mapping id: {getattr(mapping, 'id', 'unknown')})")
                    continue
                
                # Look up song using pre-built dictionary (using hash as primary key)
                # Handle missing or invalid hash gracefully (no referential integrity in legacy DB)
                song = song_hash_lookup.get(mapping.hash) if mapping.hash else None
                if not song:
                    skipped_no_song += 1
                    if skipped_no_song <= 10:  # Only show first 10 warnings
                        print(f"Song does not exist for hash '{mapping.hash}' (mapping id: {getattr(mapping, 'id', 'unknown')})")
                    continue
                
                # Track artist-song association
                artist_song_associations[artist.id].add(song.id)
                successful_associations += 1
                
                # Prepare artist comment if description exists
                # Handle missing profile gracefully (data integrity issues from legacy DB)
                if mapping.description and mapping.description.strip():
                    if artist.profile:
                        comment_counter += 1
                        artist_comment = ArtistComment(
                            profile=artist.profile,
                            song=song,
                            text=mapping.description.strip()
                        )
                        artist_comments_to_create.append(artist_comment)
                    else:
                        skipped_no_profile += 1
                        if skipped_no_profile <= 10:  # Track separately
                            print(f"Artist {artist.id} has no profile for comment (mapping id: {getattr(mapping, 'id', 'unknown')})")
                
                # Bulk create when batch is full or at the end
                if len(artist_comments_to_create) >= batch_size or counter == total:
                    if artist_comments_to_create or artist_song_associations:
                        self.bulk_create_batch(
                            artist_comments_to_create,
                            artist_song_associations
                        )
                    
                    if counter % 5000 == 0 or counter == total:
                        print(f"Processed {counter} out of {total} mappings. "
                              f"Successful: {successful_associations}, "
                              f"Comments: {comment_counter}, "
                              f"Skipped (no artist): {skipped_no_artist}, "
                              f"Skipped (no song): {skipped_no_song}, "
                              f"Skipped (no profile): {skipped_no_profile}")
                    
                    # Clear batches
                    artist_comments_to_create = []
                    artist_song_associations = defaultdict(set)
            
            print(f"Migration complete! Processed {counter} mappings")
            print(f"  Successful associations: {successful_associations}")
            print(f"  Comments created: {comment_counter}")
            print(f"  Skipped due to missing artist: {skipped_no_artist}")
            print(f"  Skipped due to missing song: {skipped_no_song}")
            print(f"  Skipped due to missing profile: {skipped_no_profile}")
            
            # Show percentage of successful processing
            if counter > 0:
                success_rate = (successful_associations / counter) * 100
                print(f"  Success rate: {success_rate:.1f}%")

    def build_song_hash_lookup(self):
        """Build a dictionary mapping song hash to Song objects for fast lookup"""
        print("Building song hash lookup dictionary...")
        song_lookup = {}
        duplicate_hashes = 0
        
        # Get all songs with their hashes
        for song in Song.objects.all().iterator(chunk_size=1000):
            if song.hash and song.hash.strip():  # Only include non-empty hashes
                hash_key = song.hash.strip()
                if hash_key in song_lookup:
                    duplicate_hashes += 1
                    if duplicate_hashes <= 5:  # Show first few duplicates
                        print(f"Warning: Duplicate hash found: {hash_key} (keeping first occurrence)")
                else:
                    song_lookup[hash_key] = song
        
        if duplicate_hashes > 5:
            print(f"Warning: Found {duplicate_hashes} total duplicate hashes")
            
        return song_lookup

    def build_artist_id_lookup(self):
        """Build a dictionary mapping legacy artist ID to Artist objects for fast lookup"""
        print("Building artist ID lookup dictionary...")
        artist_lookup = {}
        duplicate_ids = 0
        artists_without_profile = 0
        
        # Get all artists with their legacy IDs
        for artist in Artist.objects.select_related('profile').all().iterator(chunk_size=1000):
            if artist.legacy_id is not None:  # Handle legacy_id = 0 as valid
                if artist.legacy_id in artist_lookup:
                    duplicate_ids += 1
                    if duplicate_ids <= 5:  # Show first few duplicates
                        print(f"Warning: Duplicate legacy_id found: {artist.legacy_id} (keeping first occurrence)")
                else:
                    artist_lookup[artist.legacy_id] = artist
                    
                # Track artists without profiles (potential data integrity issue)
                if not artist.profile:
                    artists_without_profile += 1
        
        if duplicate_ids > 5:
            print(f"Warning: Found {duplicate_ids} total duplicate legacy IDs")
        if artists_without_profile > 0:
            print(f"Warning: Found {artists_without_profile} artists without profiles")
            
        return artist_lookup

    def bulk_create_batch(self, artist_comments_to_create, artist_song_associations):
        """Bulk create artist comments and artist-song associations"""
        
        with transaction.atomic():
            try:
                # Bulk create artist comments
                if artist_comments_to_create:
                    try:
                        created_comments = ArtistComment.objects.bulk_create(artist_comments_to_create)
                        print(f"  Created {len(created_comments)} artist comments")
                    except Exception as comment_error:
                        print(f"Bulk comment creation failed: {comment_error}")
                        # Fall back to individual creation
                        successful_comments = 0
                        for comment in artist_comments_to_create:
                            try:
                                ArtistComment.objects.create(
                                    profile=comment.profile,
                                    song=comment.song,
                                    text=comment.text
                                )
                                successful_comments += 1
                            except IntegrityError as e:
                                print(f"Failed to create comment for profile {comment.profile.id} and song {comment.song.id}: {e}")
                            except Exception as e:
                                print(f"Unexpected error creating comment: {e}")
                        print(f"  Created {successful_comments} comments individually")
                
                # Handle artist-song associations
                if artist_song_associations:
                    association_count = 0
                    failed_associations = 0
                    for artist_id, song_ids in artist_song_associations.items():
                        try:
                            # Verify artist still exists (defensive programming for data integrity)
                            artist = Artist.objects.get(id=artist_id)
                            
                            # Verify songs still exist and filter out any that don't
                            songs = Song.objects.filter(id__in=song_ids)
                            existing_song_ids = set(songs.values_list('id', flat=True))
                            missing_song_ids = song_ids - existing_song_ids
                            
                            if missing_song_ids:
                                print(f"Warning: {len(missing_song_ids)} songs no longer exist for artist {artist_id}")
                            
                            if songs.exists():
                                # Only add existing songs
                                artist.songs.add(*songs)
                                association_count += len(existing_song_ids)
                            else:
                                failed_associations += 1
                                
                        except Artist.DoesNotExist:
                            print(f"Artist {artist_id} no longer exists during association")
                            failed_associations += 1
                        except Exception as e:
                            print(f"Failed to create associations for artist {artist_id}: {e}")
                            failed_associations += 1
                    
                    print(f"  Created {association_count} artist-song associations")
                    if failed_associations > 0:
                        print(f"  Failed to create associations for {failed_associations} artists")
                    
            except Exception as e:
                print(f"Error during bulk creation: {str(e)}")
                import traceback
                traceback.print_exc()
