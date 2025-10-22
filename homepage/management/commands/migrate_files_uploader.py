from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction, IntegrityError

from homepage import legacy_models
from homepage.models import Profile
from songs.models import Song
from .disable_signals import DisableSignals

class Command(BaseCommand):
    help = "Migrate the legacy files_uploader table"

    def handle(self, *args, **options):
        with DisableSignals():
            # Use iterator() to avoid loading all records into memory
            files_uploader_queryset = legacy_models.TmaFilesUploader.objects.using('legacy').all()
            total = files_uploader_queryset.count()
            
            print(f"Starting migration of {total} files_uploader records.")
            print("Building lookup dictionaries...")
            
            # Pre-build lookup dictionaries for efficient access (no foreign keys in legacy DB)
            profile_lookup = self.build_profile_lookup()
            song_lookup = self.build_song_lookup()
            
            print(f"Built lookup dictionaries: {len(profile_lookup)} profiles, {len(song_lookup)} songs")
            
            batch_size = 1000
            songs_to_update = []
            
            counter = 0
            skipped_no_profile = 0
            skipped_no_song = 0
            successful_uploaders = 0
            anonymous_uploaders = 0
            
            print("Processing files_uploader records...")
            
            # Process in batches for better performance
            for file_uploader in files_uploader_queryset.iterator(chunk_size=batch_size):
                counter += 1
                
                song_update_data = self.prepare_song_update_data(file_uploader, profile_lookup, song_lookup)
                
                if song_update_data is not None:
                    songs_to_update.append(song_update_data)
                    successful_uploaders += 1
                    
                    # Track anonymous uploaders
                    if song_update_data.uploaded_by is None:
                        anonymous_uploaders += 1
                else:
                    # Track skipped records (already logged in prepare_song_update_data)
                    if not self.is_valid_profile(file_uploader.userid, profile_lookup):
                        skipped_no_profile += 1
                    if not self.is_valid_song(file_uploader.moduleid, song_lookup):
                        skipped_no_song += 1
                
                # Bulk update when batch is full or at the end
                if len(songs_to_update) >= batch_size or counter == total:
                    if songs_to_update:
                        self.bulk_update_batch(songs_to_update)
                    
                    if counter % 5000 == 0 or counter == total:
                        print(f"Processed {counter} out of {total} files_uploader records. "
                              f"Successful: {successful_uploaders}, "
                              f"Anonymous: {anonymous_uploaders}, "
                              f"Skipped (no profile): {skipped_no_profile}, "
                              f"Skipped (no song): {skipped_no_song}")
                    
                    # Clear batch
                    songs_to_update = []
            
            print(f"Migration complete! Processed {counter} files_uploader records")
            print(f"  Successful uploader assignments: {successful_uploaders}")
            print(f"  Anonymous uploaders: {anonymous_uploaders}")
            print(f"  Skipped due to missing profile: {skipped_no_profile}")
            print(f"  Skipped due to missing song: {skipped_no_song}")
            
            # Show percentage of successful processing
            if counter > 0:
                success_rate = (successful_uploaders / counter) * 100
                print(f"  Success rate: {success_rate:.1f}%")

    def build_profile_lookup(self):
        """Build a dictionary mapping legacy profile ID to Profile objects for fast lookup"""
        print("Building profile lookup dictionary...")
        profile_lookup = {}
        
        # Get all profiles with their legacy IDs
        for profile in Profile.objects.all().iterator(chunk_size=1000):
            if profile.legacy_id is not None:  # Handle legacy_id = 0 as valid
                profile_lookup[profile.legacy_id] = profile
        
        return profile_lookup

    def build_song_lookup(self):
        """Build a dictionary mapping legacy song ID to Song objects for fast lookup"""
        print("Building song lookup dictionary...")
        song_lookup = {}
        
        # Get all songs with their legacy IDs
        for song in Song.objects.all().iterator(chunk_size=1000):
            if song.legacy_id is not None:  # Handle legacy_id = 0 as valid
                song_lookup[song.legacy_id] = song
        
        return song_lookup

    def is_valid_profile(self, userid, profile_lookup):
        """Check if profile is valid (special handling for userid 1 - anonymous)"""
        if userid == 1:
            return True  # Anonymous uploaders are allowed
        return userid and userid in profile_lookup

    def is_valid_song(self, moduleid, song_lookup):
        """Check if song ID exists in lookup"""
        return moduleid and moduleid in song_lookup

    def prepare_song_update_data(self, file_uploader, profile_lookup, song_lookup):
        """Prepare Song object for bulk update with uploader data"""
        
        # Handle profile with special case for anonymous uploaders (no referential integrity in legacy DB)
        profile = None
        if file_uploader.userid and file_uploader.userid != 1:  # userid 1 = anonymous
            if file_uploader.userid in profile_lookup:
                profile = profile_lookup[file_uploader.userid]
            else:
                print(f"Could not find profile for userid {file_uploader.userid} and song id {file_uploader.moduleid}")
                return None  # Skip this record
        # If userid == 1, profile remains None (anonymous uploader)
        
        # Handle song lookup (no referential integrity in legacy DB)
        if not file_uploader.moduleid or file_uploader.moduleid not in song_lookup:
            print(f"Could not find song for userid {file_uploader.userid} and song id {file_uploader.moduleid}")
            return None  # Skip this record
        
        song = song_lookup[file_uploader.moduleid]
        
        # Update song uploader field
        song.uploaded_by = profile  # Can be None for anonymous uploaders
        
        return song

    def bulk_update_batch(self, songs_to_update):
        """Bulk update songs with uploader data"""
        
        with transaction.atomic():
            try:
                # Bulk update songs
                try:
                    updated_count = Song.objects.bulk_update(
                        songs_to_update, 
                        ['uploaded_by']
                    )
                    print(f"  Updated {updated_count} songs with uploader data")
                except Exception as update_error:
                    print(f"Bulk song update failed: {update_error}")
                    # Fall back to individual updates
                    successful_updates = 0
                    for song in songs_to_update:
                        try:
                            Song.objects.filter(id=song.id).update(
                                uploaded_by=song.uploaded_by
                            )
                            successful_updates += 1
                        except IntegrityError as e:
                            uploader_info = f"profile {song.uploaded_by.id}" if song.uploaded_by else "anonymous"
                            print(f"Failed to update song {song.id} with uploader {uploader_info}: {e}")
                        except Exception as e:
                            print(f"Unexpected error updating song {song.id}: {e}")
                    print(f"  Updated {successful_updates} songs individually")
                    
            except Exception as e:
                print(f"Error during bulk update: {str(e)}")
                import traceback
                traceback.print_exc()
