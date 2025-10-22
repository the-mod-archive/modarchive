from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction

from homepage import legacy_models
from homepage.models import Profile
from uploads.models import NewSong
from .disable_signals import DisableSignals

class Command(BaseCommand):
    help = "Migrate the legacy files_new table"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pre-compute flag mapping for better performance
        self._flag_mapping = {
            'yellow': NewSong.Flags.NEEDS_SECOND_OPINION,
            'green': NewSong.Flags.PRE_SCREENED_PLUS,
            'grey': NewSong.Flags.PRE_SCREENED,
            'blue': NewSong.Flags.UNDER_INVESTIGATION,
            'orange': NewSong.Flags.POSSIBLE_DUPLICATE,
        }

    def handle(self, *args, **options):
        with DisableSignals():
            # Use iterator() to avoid loading all records into memory
            files_queryset = legacy_models.FilesNew.objects.using('legacy').all().order_by('id')
            total = files_queryset.count()
            
            print(f"Starting migrations of {total} files from files_new.")
            print("Building profile lookup dictionary...")
            
            # Pre-build profile lookup dictionary for efficient access
            profile_lookup = self.build_profile_lookup()
            
            print(f"Built profile lookup: {len(profile_lookup)} profiles")
            
            batch_size = 1000
            new_songs_to_create = []
            
            counter = 0
            skipped_no_uploader = 0
            skipped_no_flagger = 0
            successful_songs = 0
            
            print("Processing files...")
            
            # Process in batches for better performance
            for file in files_queryset.iterator(chunk_size=batch_size):
                counter += 1
                
                song_data = self.prepare_new_song_data(file, profile_lookup)
                
                if song_data is not None:
                    new_songs_to_create.append(song_data)
                    successful_songs += 1
                else:
                    # Track skipped records (already logged in prepare_new_song_data)
                    if not self.is_valid_uploader(file.uploader_uid, profile_lookup):
                        skipped_no_uploader += 1
                    if file.flagged_by and not self.is_valid_profile(file.flagged_by, profile_lookup):
                        skipped_no_flagger += 1
                
                # Bulk create when batch is full or at the end
                if len(new_songs_to_create) >= batch_size or counter == total:
                    if new_songs_to_create:
                        self.bulk_create_batch(new_songs_to_create)
                    
                    if counter % 5000 == 0 or counter == total:
                        print(f"Processed {counter} out of {total} files. "
                              f"Successful: {successful_songs}, "
                              f"Skipped (no uploader): {skipped_no_uploader}, "
                              f"Skipped (no flagger): {skipped_no_flagger}")
                    
                    # Clear batch
                    new_songs_to_create = []
            
            print(f"Migration complete! Processed {counter} files")
            print(f"  Successful new songs: {successful_songs}")
            print(f"  Skipped due to missing uploader: {skipped_no_uploader}")
            print(f"  Skipped due to missing flagger: {skipped_no_flagger}")
            
            # Show percentage of successful processing
            if counter > 0:
                success_rate = (successful_songs / counter) * 100
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

    def get_flag_mapping(self, flag_string):
        """Get flag enum value from string using pre-computed mapping"""
        if not flag_string:
            return None
        return self._flag_mapping.get(flag_string.lower(), None)

    def is_valid_uploader(self, uploader_uid, profile_lookup):
        """Check if uploader is valid (special handling for uid 1 and 0)"""
        if uploader_uid == 1:
            return True  # Special case: uid 1 is considered valid but maps to None
        if uploader_uid == 0:
            return False  # uid 0 is invalid
        return uploader_uid in profile_lookup

    def is_valid_profile(self, profile_id, profile_lookup):
        """Check if profile ID exists in lookup"""
        return profile_id and profile_id in profile_lookup

    def prepare_new_song_data(self, file, profile_lookup):
        """Prepare NewSong data object for bulk creation"""
        
        # Handle uploader profile with special cases (no referential integrity in legacy DB)
        uploader_profile = None
        if file.uploader_uid and file.uploader_uid != 1:  # uid 1 maps to None
            if file.uploader_uid in profile_lookup:
                uploader_profile = profile_lookup[file.uploader_uid]
            else:
                if file.uploader_uid != 0:  # Don't warn for uid 0
                    print(f"Could not find profile for uploader_uid {file.uploader_uid} (file id: {getattr(file, 'id', 'unknown')})")
                return None  # Skip this record
        
        # Handle flagged_by profile (no referential integrity in legacy DB)
        flagged_by = None
        if file.flagged_by:
            if file.flagged_by in profile_lookup:
                flagged_by = profile_lookup[file.flagged_by]
            else:
                print(f"Could not find profile for flagged_by {file.flagged_by} (file id: {getattr(file, 'id', 'unknown')}). Setting to None.")
                # Don't return None here - just set flagged_by to None and continue
        
        # Get flag mapping
        flag = self.get_flag_mapping(file.flag)
        
        # Extract format from filename
        format_ext = file.filename.split('.')[-1] if file.filename and '.' in file.filename else ''
        
        # Create NewSong object
        new_song = NewSong(
            filename=file.filename,
            filename_unzipped=file.filename_unzipped,
            title=file.songtitle,
            format=format_ext,
            file_size=file.filesize,
            channels=file.channels,
            instrument_text=file.insttext,
            comment_text=file.comment,
            hash=file.hash,
            pattern_hash=file.patternhash,
            artist_from_file=file.artist_file,
            uploader_profile=uploader_profile,
            uploader_ip_address=file.uploader,
            is_by_uploader=file.ismine,
            create_date=file.dateuploaded,
            flag=flag,
            flagged_by=flagged_by
        )
        
        return new_song

    def bulk_create_batch(self, new_songs_to_create):
        """Bulk create new songs"""
        
        with transaction.atomic():
            try:
                # Bulk create new songs
                try:
                    created_songs = NewSong.objects.bulk_create(new_songs_to_create)
                    print(f"  Created {len(created_songs)} new songs")
                except Exception as song_error:
                    print(f"Bulk song creation failed: {song_error}")
                    # Fall back to individual creation
                    successful_songs = 0
                    for song in new_songs_to_create:
                        try:
                            NewSong.objects.create(
                                filename=song.filename,
                                filename_unzipped=song.filename_unzipped,
                                title=song.title,
                                format=song.format,
                                file_size=song.file_size,
                                channels=song.channels,
                                instrument_text=song.instrument_text,
                                comment_text=song.comment_text,
                                hash=song.hash,
                                pattern_hash=song.pattern_hash,
                                artist_from_file=song.artist_from_file,
                                uploader_profile=song.uploader_profile,
                                uploader_ip_address=song.uploader_ip_address,
                                is_by_uploader=song.is_by_uploader,
                                create_date=song.create_date,
                                flag=song.flag,
                                flagged_by=song.flagged_by
                            )
                            successful_songs += 1
                        except Exception as e:
                            print(f"Failed to create new song {song.filename}: {e}")
                    print(f"  Created {successful_songs} new songs individually")
                    
            except Exception as e:
                print(f"Error during bulk creation: {str(e)}")
                import traceback
                traceback.print_exc()
