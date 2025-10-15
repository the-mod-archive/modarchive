from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.db import transaction, IntegrityError

from homepage import legacy_models
from homepage.models import Profile
from songs.models import Song

class Command(BaseCommand):
    help = "Migrate the legacy nominations table"

    def handle(self, *args, **options):
        # Use iterator() to avoid loading all records into memory
        nominations_queryset = legacy_models.TmaNominations.objects.using('legacy').all().order_by('id')
        total = nominations_queryset.count()
        
        print(f"Starting migration of {total} nominations.")
        print("Building lookup dictionaries...")
        
        # Pre-build lookup dictionaries for efficient access (no foreign keys in legacy DB)
        song_hash_lookup = self.build_song_hash_lookup()
        profile_lookup = self.build_profile_lookup()
        
        print(f"Built lookup dictionaries: {len(song_hash_lookup)} songs, {len(profile_lookup)} profiles")
        
        batch_size = 1000
        songs_to_update = []
        
        counter = 0
        skipped_no_song = 0
        skipped_multiple_songs = 0
        skipped_no_profile = 0
        successful_nominations = 0
        anonymous_nominations = 0
        
        print("Processing nominations...")
        
        # Process in batches for better performance
        for nomination in nominations_queryset.iterator(chunk_size=batch_size):
            counter += 1
            
            song_update_data = self.prepare_song_update_data(nomination, song_hash_lookup, profile_lookup)
            
            if song_update_data is not None:
                songs_to_update.append(song_update_data)
                successful_nominations += 1
                
                # Track anonymous nominations
                if song_update_data.featured_by is None:
                    anonymous_nominations += 1
            else:
                # Track skipped records (already logged in prepare_song_update_data)
                if nomination.hash not in song_hash_lookup:
                    skipped_no_song += 1
                elif len(song_hash_lookup.get(nomination.hash, [])) > 1:
                    skipped_multiple_songs += 1
                elif not self.is_valid_profile(nomination.userid, profile_lookup):
                    skipped_no_profile += 1
            
            # Bulk update when batch is full or at the end
            if len(songs_to_update) >= batch_size or counter == total:
                if songs_to_update:
                    self.bulk_update_batch(songs_to_update)
                
                if counter % 5000 == 0 or counter == total:
                    print(f"Processed {counter} out of {total} nominations. "
                          f"Successful: {successful_nominations}, "
                          f"Anonymous: {anonymous_nominations}, "
                          f"Skipped (no song): {skipped_no_song}, "
                          f"Skipped (multiple songs): {skipped_multiple_songs}, "
                          f"Skipped (no profile): {skipped_no_profile}")
                
                # Clear batch
                songs_to_update = []
        
        print(f"Migration complete! Processed {counter} nominations")
        print(f"  Successful nominations: {successful_nominations}")
        print(f"  Anonymous nominations: {anonymous_nominations}")
        print(f"  Skipped due to missing song: {skipped_no_song}")
        print(f"  Skipped due to multiple songs: {skipped_multiple_songs}")
        print(f"  Skipped due to missing profile: {skipped_no_profile}")
        
        # Show percentage of successful processing
        if counter > 0:
            success_rate = (successful_nominations / counter) * 100
            print(f"  Success rate: {success_rate:.1f}%")

    def build_song_hash_lookup(self):
        """Build a dictionary mapping song hashes to Song objects for fast lookup"""
        print("Building song hash lookup dictionary...")
        song_hash_lookup = {}
        
        # Get all songs with their hashes - handle potential hash collisions
        for song in Song.objects.all().iterator(chunk_size=1000):
            if song.hash:
                if song.hash not in song_hash_lookup:
                    song_hash_lookup[song.hash] = []
                song_hash_lookup[song.hash].append(song)
        
        # Report hash collisions
        collisions = sum(1 for songs in song_hash_lookup.values() if len(songs) > 1)
        if collisions > 0:
            print(f"Warning: Found {collisions} hash collisions in song database")
        
        return song_hash_lookup

    def build_profile_lookup(self):
        """Build a dictionary mapping legacy profile ID to Profile objects for fast lookup"""
        print("Building profile lookup dictionary...")
        profile_lookup = {}
        
        # Get all profiles with their legacy IDs
        for profile in Profile.objects.all().iterator(chunk_size=1000):
            if profile.legacy_id is not None:  # Handle legacy_id = 0 as valid
                profile_lookup[profile.legacy_id] = profile
        
        return profile_lookup

    def is_valid_profile(self, userid, profile_lookup):
        """Check if profile is valid (special handling for userid 1 - anonymous)"""
        if userid == 1:
            return True  # Anonymous nominations are allowed
        return userid and userid in profile_lookup

    def prepare_song_update_data(self, nomination, song_hash_lookup, profile_lookup):
        """Prepare Song object for bulk update with nomination data"""
        
        # Handle song lookup with hash collision detection (no referential integrity in legacy DB)
        if not nomination.hash or nomination.hash not in song_hash_lookup:
            print(f"Could not find song for hash {nomination.hash} (nomination id: {getattr(nomination, 'id', 'unknown')})")
            return None  # Skip this record
        
        songs_with_hash = song_hash_lookup[nomination.hash]
        if len(songs_with_hash) > 1:
            print(f"Multiple songs found for hash {nomination.hash} (nomination id: {getattr(nomination, 'id', 'unknown')})")
            return None  # Skip this record - can't determine which song to update
        
        song = songs_with_hash[0]
        
        # Handle profile with special case for anonymous nominations (no referential integrity in legacy DB)
        profile = None
        if nomination.userid and nomination.userid != 1:  # userid 1 = anonymous
            if nomination.userid in profile_lookup:
                profile = profile_lookup[nomination.userid]
            else:
                print(f"Could not find profile for userid {nomination.userid} (nomination id: {getattr(nomination, 'id', 'unknown')})")
                # Continue with None profile - treat as anonymous
        # If userid == 1, profile remains None (anonymous nomination)
        
        # Update song fields
        song.is_featured = True
        song.featured_date = nomination.date
        song.featured_by = profile  # Can be None for anonymous nominations
        
        return song

    def bulk_update_batch(self, songs_to_update):
        """Bulk update songs with nomination data"""
        
        with transaction.atomic():
            try:
                # Bulk update songs
                try:
                    updated_count = Song.objects.bulk_update(
                        songs_to_update, 
                        ['is_featured', 'featured_date', 'featured_by']
                    )
                    print(f"  Updated {updated_count} songs with nomination data")
                except Exception as update_error:
                    print(f"Bulk song update failed: {update_error}")
                    # Fall back to individual updates
                    successful_updates = 0
                    for song in songs_to_update:
                        try:
                            Song.objects.filter(id=song.id).update(
                                is_featured=song.is_featured,
                                featured_date=song.featured_date,
                                featured_by=song.featured_by
                            )
                            successful_updates += 1
                        except IntegrityError as e:
                            profile_info = f"profile {song.featured_by.id}" if song.featured_by else "anonymous"
                            print(f"Failed to update song {song.id} with nomination from {profile_info}: {e}")
                        except Exception as e:
                            print(f"Unexpected error updating song {song.id}: {e}")
                    print(f"  Updated {successful_updates} songs individually")
                    
            except Exception as e:
                print(f"Error during bulk update: {str(e)}")
                import traceback
                traceback.print_exc()