import os
from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.db import transaction, Error
from django.shortcuts import redirect
from django.views import View
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.utils import timezone
from django.urls.base import reverse

from songs.models import Song
from uploads.models import NewSong, ScreeningEvent
from uploads import constants
from artists.models import Artist

class ScreeningActionView(PermissionRequiredMixin, View):
    template_name = 'screening_action_result.html'
    permission_required = 'uploads.can_approve_songs'

    class ScreeningAction:
        CLAIM = constants.CLAIM_KEYWORD
        UNCLAIM = constants.UNCLAIM_KEYWORD
        PRE_SCREEN = constants.PRE_SCREEN_KEYWORD
        PRE_SCREEN_AND_RECOMMEND = constants.PRE_SCREEN_AND_RECOMMEND_KEYWORD
        NEEDS_SECOND_OPINION = constants.NEEDS_SECOND_OPINION_KEYWORD
        POSSIBLE_DUPLICATE = constants.POSSIBLE_DUPLICATE_KEYWORD
        UNDER_INVESTIGATION = constants.UNDER_INVESTIGATION_KEYWORD
        APPROVE = constants.APPROVE_KEYWORD
        APPROVE_AND_FEATURE = constants.APPROVE_AND_FEATURE_KEYWORD
        REJECT = constants.REJECT_KEYWORD
        CLEAR_FLAG = constants.CLEAR_FLAG_KEYWORD
        RENAME = constants.RENAME_KEYWORD

    def post(self, request, *args, **kwargs):
        # Determine action from request, reject if not a valid action
        action = getattr(self.ScreeningAction, request.POST.get('action', '').upper(), None)

        selected_songs = request.POST.getlist('selected_songs')
        songs = NewSong.objects.filter(id__in=selected_songs)

        if len(songs) == 0:
            messages.warning(request, constants.MESSAGE_NO_SONGS_SELECTED)
            return redirect('screening_index')

        my_claimed_songs_queryset = songs.filter(claimed_by=request.user.profile)

        match action:
            case self.ScreeningAction.CLAIM:
                return self.claim(songs, request)
            case self.ScreeningAction.UNCLAIM:
                return self.unclaim(my_claimed_songs_queryset, request)
            case self.ScreeningAction.PRE_SCREEN:
                return self.apply_flag(my_claimed_songs_queryset, request, NewSong.Flags.PRE_SCREENED, constants.PRE_SCREENED_FILTER)
            case self.ScreeningAction.PRE_SCREEN_AND_RECOMMEND:
                return self.apply_flag(my_claimed_songs_queryset, request, NewSong.Flags.PRE_SCREENED_PLUS, constants.PRE_SCREENED_AND_RECOMMENDED_FILTER)
            case self.ScreeningAction.NEEDS_SECOND_OPINION:
                return self.apply_flag(my_claimed_songs_queryset, request, NewSong.Flags.NEEDS_SECOND_OPINION, constants.NEEDS_SECOND_OPINION_FILTER)
            case self.ScreeningAction.POSSIBLE_DUPLICATE:
                return self.apply_flag(my_claimed_songs_queryset, request, NewSong.Flags.POSSIBLE_DUPLICATE, constants.POSSIBLE_DUPLICATE_FILTER)
            case self.ScreeningAction.UNDER_INVESTIGATION:
                return self.apply_flag(my_claimed_songs_queryset, request, NewSong.Flags.UNDER_INVESTIGATION, constants.UNDER_INVESTIGATION_FILTER)
            case self.ScreeningAction.APPROVE:
                return self.approve_songs(songs, request)
            case self.ScreeningAction.APPROVE_AND_FEATURE:
                return self.approve_songs(songs, request, feature=True)
            case self.ScreeningAction.REJECT:
                song_ids_str = ','.join(selected_songs)
                query_string = urlencode({'song_ids': song_ids_str})
                return redirect(f'{reverse("screening_reject")}?{query_string}')
            case self.ScreeningAction.CLEAR_FLAG:
                return self.clear_flag(my_claimed_songs_queryset, request)
            case self.ScreeningAction.RENAME:
                if len(songs) > 1:
                    messages.warning(request, constants.RENAME_SCREENING_ONE_SONG_ONLY)
                    return redirect('screen_song', pk=my_claimed_songs_queryset[0].id)

                if len(my_claimed_songs_queryset) == 0:
                    messages.warning(request, constants.RENAME_SCREENING_REQUIRES_CLAIM)
                    return redirect('screen_song', pk=songs[0].id)

                return redirect('screening_rename', pk=my_claimed_songs_queryset[0].id)

        # Redirect to screening view
        return redirect('screening_index')

    def claim(self, songs, request):
        queryset = songs.filter(claimed_by=None)
        if len(queryset) == 0:
            return redirect('screening_index')

        songs_to_update = list(queryset)

        queryset.update(
            claimed_by=request.user.profile,
            claim_date=timezone.now()
        )

        screening_events = [
            ScreeningEvent(
                new_song=song,
                profile=request.user.profile,
                type=ScreeningEvent.Types.CLAIM,
                content=f'Claimed by {request.user.profile.display_name}'
            )
            for song in songs_to_update
        ]
        ScreeningEvent.objects.bulk_create(screening_events)
        return redirect(f'{reverse("screening_index")}?filter={constants.MY_SCREENING_FILTER}')

    def unclaim(self, queryset, request):
        songs_to_update = list(queryset)

        queryset.update(
            claimed_by=None,
            claim_date=None
        )

        screening_events = [
            ScreeningEvent(
                new_song=song,
                profile=request.user.profile,
                type=ScreeningEvent.Types.UNCLAIM,
                content=f'Unclaimed by {request.user.profile.display_name}'
            )
            for song in songs_to_update
        ]
        ScreeningEvent.objects.bulk_create(screening_events)

        return redirect('screening_index')

    def apply_flag(self, my_claimed_songs_queryset, request, flag, return_filter):
        if len(my_claimed_songs_queryset) == 0:
            return redirect('screening_index')

        songs_to_update = list(my_claimed_songs_queryset)

        my_claimed_songs_queryset.update(
            claimed_by=None,
            claim_date=None,
            flag=flag,
            flagged_by=request.user.profile
        )

        screening_events = [
            ScreeningEvent(
                new_song=song,
                profile=request.user.profile,
                type=ScreeningEvent.Types.APPLY_FLAG,
                content=f'Flag set to {flag} by {request.user.profile.display_name} (was {song.flag})'
            )
            for song in songs_to_update
        ]
        ScreeningEvent.objects.bulk_create(screening_events)

        return redirect(f'{reverse("screening_index")}?filter={return_filter}')

    def clear_flag(self, queryset, request):
        if len(queryset) == 0:
            return redirect('screening_index')

        songs_to_update = list(queryset)

        queryset.update(
            claimed_by=None,
            claim_date=None,
            flag=None,
            flagged_by=None
        )

        screening_events = [
            ScreeningEvent(
                new_song=song,
                profile=request.user.profile,
                type=ScreeningEvent.Types.CLEAR_FLAG,
                content=f'Flag cleared by {request.user.profile.display_name} (previously set to {song.flag})'
            )
            for song in songs_to_update
        ]
        ScreeningEvent.objects.bulk_create(screening_events)
        return redirect('screening_index')

    def approve_songs(self, songs, request, feature=False):
        # Bulk approval has different validation rules from single approval
        # In particular, bulk approval requires that all songs be pre-screened
        if len(songs) > 1 and not self.validate_bulk_approval(songs, request):
            base_url = reverse("screening_index")
            query_string = urlencode({'filter': constants.PRE_SCREENED_FILTER})
            return redirect(f'{base_url}?{query_string}')

        if len(songs) == 1 and not self.validate_single_approval(songs, request):
            return redirect('screen_song', pk=songs[0].id)

        pks = []
        for approved_song in songs:
            pk = self.finalize_approval(approved_song, feature, request.user.profile)
            if pk:
                pks.append(pk)

        if len(pks) > 1:
            messages.success(request, constants.MESSAGE_SONGS_APPROVED.format(len(pks)))
            return redirect('screening_index')
        elif len(pks) == 1:
            return redirect('view_song', pk=pks[0])

    @transaction.atomic
    def finalize_approval(self, approved_song: NewSong, feature=False, approver=None):
        # Folder is the capitalized first character of the filename. If it's a number, use '1_9'
        if approved_song.filename[0].isdigit():
            folder = '0_9'
        else:
            folder = approved_song.filename[0].upper()

        if approved_song.title.strip():
            title = approved_song.title
        else:
            title = approved_song.filename

        song = Song(
            filename=approved_song.filename,
            filename_unzipped=approved_song.filename_unzipped,
            title=title,
            title_from_file=approved_song.title,
            format=approved_song.format.upper(),
            file_size=approved_song.file_size,
            channels=approved_song.channels,
            instrument_text=approved_song.instrument_text,
            comment_text=approved_song.comment_text,
            hash=approved_song.hash,
            pattern_hash=approved_song.pattern_hash,
            folder=folder,
            uploaded_by=approved_song.uploader_profile,
            featured_by=approver if feature else None,
            featured_date=timezone.now() if feature else None,
        )

        # Move file into the new directory
        current_location = os.path.join(settings.NEW_FILE_DIR, f'{approved_song.filename}.zip')
        new_location = song.get_archive_path()
        try:
            os.rename(current_location, new_location)
        except OSError:
            return None

        try:
            song.save()

            # If uploaded by artist, add to artist's list of songs
            if approved_song.is_by_uploader:
                # Determine if the uploader profile has an artist
                if not Artist.objects.filter(profile=approved_song.uploader_profile).exists():
                    # If not, create a new artist
                    artist = Artist.objects.create(
                        user=approved_song.uploader_profile.user,
                        profile=approved_song.uploader_profile,
                        name=approved_song.uploader_profile.user.username
                    )
                else:
                    # If so, use the existing one
                    artist = approved_song.uploader_profile.artist

                artist.songs.add(song)

            # Delete the NewSong record
            approved_song.delete()
            return song.pk
        except Error:
            os.rename(new_location, current_location)
            transaction.set_rollback(True)
            return None

    def validate_bulk_approval(self, songs, request) -> bool:
        if songs.exclude(flag=NewSong.Flags.PRE_SCREENED).exclude(flag=NewSong.Flags.PRE_SCREENED_PLUS).exists():
            messages.warning(request, constants.MESSAGE_ALL_SONGS_MUST_BE_PRESCREENED_FOR_BULK_APPROVAL)
        elif Song.objects.filter(filename__in=songs.values_list('filename', flat=True)).exists():
            messages.warning(request, constants.MESSAGE_ALL_SONGS_MUST_HAVE_UNIQUE_FILENAME_FOR_BULK_APPROVAL)
        elif Song.objects.filter(hash__in=songs.values_list('hash', flat=True)).exists():
            messages.warning(request, constants.MESSAGE_ALL_SONGS_MUST_HAVE_UNIQUE_HASH_FOR_BULK_APPROVAL)
        elif songs.exclude(claimed_by=request.user.profile).filter(claimed_by__isnull=False).exists():
            messages.warning(request, constants.MESSAGE_ALL_SONGS_MUST_NOT_BE_CLAIMED_BY_OTHERS_FOR_BULK_APPROVAL)

        if messages.get_messages(request):
            return False

        return True

    def validate_single_approval(self, songs, request) -> bool:
        approved_song = songs[0]
        if approved_song.claimed_by != request.user.profile and approved_song.flag not in [NewSong.Flags.PRE_SCREENED, NewSong.Flags.PRE_SCREENED_PLUS]:
            messages.warning(request, constants.MESSAGE_APPROVAL_REQUIRES_CLAIM)

        if approved_song.flag == NewSong.Flags.UNDER_INVESTIGATION:
            messages.warning(request, constants.MESSAGE_CANNOT_APPROVE_UNDER_INVESTIGATION)
        elif approved_song.flag == NewSong.Flags.POSSIBLE_DUPLICATE:
            messages.warning(request, constants.MESSAGE_CANNOT_APPROVE_POSSIBLE_DUPLICATE)

        if Song.objects.filter(filename=approved_song.filename).exists():
            messages.warning(request, constants.MESSAGE_CANNOT_APPROVE_DUPLICATE_FILENAME)

        if Song.objects.filter(hash=approved_song.hash).exists():
            messages.warning(request, constants.MESSAGE_CANNOT_APPROVE_DUPLICATE_HASH)

        if messages.get_messages(request):
            return False

        return True
