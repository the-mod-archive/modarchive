import os

from django.conf import settings
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import redirect
from django.views import View
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.utils import timezone

from songs.models import NewSong, Song
from songs import constants
from artists.models import Artist

class ScreeningActionView(PermissionRequiredMixin, View):
    template_name = 'screening_action_result.html'
    permission_required = 'songs.can_approve_songs'

    class ScreeningAction:
        CLAIM = constants.CLAIM_KEYWORD
        PRE_SCREEN = constants.PRE_SCREEN_KEYWORD
        PRE_SCREEN_AND_RECOMMEND = constants.PRE_SCREEN_AND_RECOMMEND_KEYWORD
        NEEDS_SECOND_OPINION = constants.NEEDS_SECOND_OPINION_KEYWORD
        POSSIBLE_DUPLICATE = constants.POSSIBLE_DUPLICATE_KEYWORD
        UNDER_INVESTIGATION = constants.UNDER_INVESTIGATION_KEYWORD
        APPROVE = constants.APPROVE_KEYWORD

    def post(self, request, *args, **kwargs):
        # Determine action from request, reject if not a valid action
        action = getattr(self.ScreeningAction, request.POST.get('action', '').upper(), None)

        selected_songs = request.POST.getlist('selected_songs')
        songs = NewSong.objects.filter(id__in=selected_songs)

        match action:
            case self.ScreeningAction.CLAIM:
                songs.filter(
                    claimed_by=None
                ).exclude(
                    Q(flagged_by=request.user.profile, flag=NewSong.Flags.NEEDS_SECOND_OPINION) |
                    Q(flagged_by=request.user.profile, flag=NewSong.Flags.POSSIBLE_DUPLICATE) |
                    Q(flagged_by=request.user.profile, flag=NewSong.Flags.UNDER_INVESTIGATION)
                ).update(
                    claimed_by=request.user.profile,
                    claim_date=timezone.now()
                )
            case self.ScreeningAction.PRE_SCREEN:
                songs.filter(
                    claimed_by=request.user.profile
                ).update(
                    claimed_by=None,
                    claim_date=None,
                    flag=NewSong.Flags.PRE_SCREENED,
                    flagged_by=request.user.profile
                )
            case self.ScreeningAction.PRE_SCREEN_AND_RECOMMEND:
                songs.filter(
                    claimed_by=request.user.profile
                ).update(
                    claimed_by=None,
                    claim_date=None,
                    flag=NewSong.Flags.PRE_SCREENED_PLUS,
                    flagged_by=request.user.profile
                )
            case self.ScreeningAction.NEEDS_SECOND_OPINION:
                songs.filter(
                    claimed_by=request.user.profile
                ).update(
                    claimed_by=None,
                    claim_date=None,
                    flag=NewSong.Flags.NEEDS_SECOND_OPINION,
                    flagged_by=request.user.profile
                )
            case self.ScreeningAction.POSSIBLE_DUPLICATE:
                songs.filter(
                    claimed_by=request.user.profile
                ).update(
                    claimed_by=None,
                    claim_date=None,
                    flag=NewSong.Flags.POSSIBLE_DUPLICATE,
                    flagged_by=request.user.profile
                )
            case self.ScreeningAction.UNDER_INVESTIGATION:
                songs.filter(
                    claimed_by=request.user.profile
                ).update(
                    claimed_by=None,
                    claim_date=None,
                    flag=NewSong.Flags.UNDER_INVESTIGATION,
                    flagged_by=request.user.profile
                )
            case self.ScreeningAction.APPROVE:
                return self.approve_songs(songs, request)

        # Redirect to screening view
        return redirect('screening_index')

    def approve_songs(self, songs, request):
        if len(songs) > 1:
            messages.warning(request, 'Approving multiple songs at once is not supported yet.')
            return redirect('screening_index')

        approved_song = songs[0]

        if not approved_song.claimed_by or approved_song.claimed_by != request.user.profile:
            messages.warning(request, constants.MESSAGE_APPROVAL_REQUIRES_CLAIM)
            return redirect('screen_song', pk=songs[0].id)

        if approved_song.flag == NewSong.Flags.UNDER_INVESTIGATION:
            messages.warning(request, constants.MESSAGE_CANNOT_APPROVE_UNDER_INVESTIGATION)
            return redirect('screen_song', pk=songs[0].id)
        elif approved_song.flag == NewSong.Flags.POSSIBLE_DUPLICATE:
            messages.warning(request, constants.MESSAGE_CANNOT_APPROVE_POSSIBLE_DUPLICATE)
            return redirect('screen_song', pk=songs[0].id)

        if Song.objects.filter(filename=approved_song.filename).exists():
            messages.warning(request, constants.MESSAGE_CANNOT_APPROVE_DUPLICATE_FILENAME)
            return redirect('screen_song', pk=songs[0].id)

        if Song.objects.filter(hash=approved_song.hash).exists():
            messages.warning(request, constants.MESSAGE_CANNOT_APPROVE_DUPLICATE_HASH)
            return redirect('screen_song', pk=songs[0].id)

        # Folder is the capitalized first character of the filename. If it's a number, use '0_9'
        if approved_song.filename[0].isdigit():
            folder = '0_9'
        else:
            folder = approved_song.filename[0].upper()

        # Move file into the new directory
        current_location = os.path.join(settings.NEW_FILE_DIR, f'{approved_song.filename}.zip')
        new_location = os.path.join(settings.MAIN_ARCHIVE_DIR, folder, f'{approved_song.filename}.zip')
        os.rename(current_location, new_location)

        # If all looks okay, add the song to the archive
        song = Song.objects.create(
            filename=approved_song.filename,
            filename_unzipped=approved_song.filename_unzipped,
            title=approved_song.title,
            format=approved_song.format.upper(),
            file_size=approved_song.file_size,
            channels=approved_song.channels,
            instrument_text=approved_song.instrument_text,
            comment_text=approved_song.comment_text,
            hash=approved_song.hash,
            pattern_hash=approved_song.pattern_hash,
            folder=folder,
        )

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

        return redirect('view_song', pk=song.pk)
