from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from songs.models import Song
from homepage.models import Profile

class NewSong(models.Model):
    class Meta:
        permissions = (
            ('can_approve_songs', "Can approve songs"),
            ('can_upload_songs', 'Can upload songs')
        )
        db_table = 'uploads_newsong'
        app_label = 'uploads'

    class Flags(models.TextChoices):
        PRE_SCREENED = 'pre-screened', _('Pre-screened')
        PRE_SCREENED_PLUS = 'pre-screened+', _('Pre-screened and recommend featured')
        NEEDS_SECOND_OPINION = 'needs-second-opinion', _('Needs second opinion')
        POSSIBLE_DUPLICATE = 'possible-duplicate', _('Possible duplicate')
        UNDER_INVESTIGATION = 'under-investigation', _('Under investigation (do not approve)')

    filename=models.CharField(max_length=120, db_index=True)
    filename_unzipped=models.CharField(max_length=120)
    title=models.CharField(max_length=120, db_index=True)
    format=models.CharField(max_length=6, choices=Song.Formats.choices, db_index=True)
    file_size=models.PositiveIntegerField()
    channels=models.PositiveSmallIntegerField()
    instrument_text=models.TextField(max_length=64000, blank=True, null=True)
    comment_text=models.TextField(max_length=64000, blank=True, null=True)
    hash=models.CharField(max_length=33)
    pattern_hash=models.CharField(max_length=16, null=True, blank=True)
    artist_from_file=models.CharField(max_length=120, null=True, blank=True)
    uploader_profile = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, blank=True)
    uploader_ip_address = models.CharField(max_length=32, default='0.0.0.0')
    is_by_uploader = models.BooleanField()
    create_date=models.DateTimeField(default=timezone.now)
    update_date=models.DateTimeField(auto_now=True)
    claimed_by=models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, blank=True, related_name='claimed_by')
    claim_date=models.DateTimeField(null=True, blank=True)
    flag=models.CharField(max_length=32, choices=Flags.choices, blank=True, null=True)
    flagged_by=models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, blank=True, related_name='flagged_by')

    def display_file_size(self):
        if self.file_size >= 1000000:
            return f'{"{:.2f}".format(self.file_size / 1000000)} MB'
        elif self.file_size >= 10000:
            return f'{"{:.2f}".format(self.file_size / 1000)} KB'

        return f'{self.file_size} bytes'

class RejectedSong(models.Model):
    class Meta:
        db_table = 'uploads_rejectedsong'
        app_label = 'uploads'

    class Reasons(models.TextChoices):
        POOR_QUALITY = 'poor-quality', _('Poor quality')
        ALREADY_EXISTS = 'already-exists', _('Already exists')
        TOO_SHORT = 'too-short', _('Too short')
        RENAME_REQUIRED = 'rename-required', _('Rename required')
        INCORRECT_FILE_EXTENSION = 'incorrect-file-extension', _('Incorrect file extension')
        PLAGIARISM = 'plagiarism', _('Plagiarism')
        CORRUPTED = 'corrupted', _('Corrupted')
        UNSUPPORTED_FORMAT = 'unsupported-format', _('Unsupported format')
        CUSTOM_MESSAGE = 'custom-message', _('Custom message')
        TEST_UPLOAD = 'test-upload', _('Test upload')
        DISPUTE = 'dispute', _('Dispute')
        DUBIOUS_CONTENT = 'dubious-content', _('Dubious content')
        TOO_BIG = 'too-big', _('Too big')
        NO_REASON_GIVEN = 'no-reason-given', _('No reason given')
        TUNING_ISSUES = 'tuning-issues', _('Tuning issues')
        MIDI_CONVERSION = 'midi-conversion', _('MIDI conversion')
        UNKNOWN = 'unknown', _('Unknown')
        OTHER = 'other', _('Other')

    reason=models.CharField(max_length=32, choices=Reasons.choices, db_index=True)
    message=models.TextField(max_length=1000, blank=True)
    is_temporary=models.BooleanField(default=False, db_index=True)
    rejected_by=models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, blank=True, related_name='screening_rejections')
    rejected_date=models.DateTimeField(default=timezone.now)
    filename=models.CharField(max_length=120, db_index=True)
    filename_unzipped=models.CharField(max_length=120)
    title=models.CharField(max_length=120, db_index=True, blank=True)
    format=models.CharField(max_length=6, choices=Song.Formats.choices, db_index=True, blank=True)
    file_size=models.PositiveIntegerField(blank=True, null=True)
    channels=models.PositiveSmallIntegerField(blank=True, null=True)
    instrument_text=models.TextField(max_length=64000, blank=True)
    comment_text=models.TextField(max_length=64000, blank=True)
    hash=models.CharField(max_length=33)
    pattern_hash=models.CharField(max_length=16, blank=True)
    artist_from_file=models.CharField(max_length=120, blank=True)
    uploader_profile = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, blank=True, related_name='rejected_uploads')
    uploader_ip_address = models.CharField(max_length=32, default='0.0.0.0', blank=True)
    is_by_uploader = models.BooleanField()
    create_date=models.DateTimeField(default=timezone.now)
    update_date=models.DateTimeField(auto_now=True)

class ScreeningEvent(models.Model):
    class Meta:
        db_table = 'uploads_screening_event'

    class Types(models.TextChoices):
        CLAIM = 'claim', _('Claim')
        UNCLAIM = 'unclaim', _('Unclaim')
        APPLY_FLAG = 'apply_flag', _('Apply Flag')
        CLEAR_FLAG = 'clear_flag', _('Clear Flag')
        RENAME = 'rename', _('Rename')

    new_song = models.ForeignKey(NewSong, on_delete=models.CASCADE, related_name='screening_events')
    profile = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, blank=True, related_name='screening_events')
    type = models.CharField(max_length=32, choices=Types.choices)
    content = models.CharField(max_length=500)
    create_date = models.DateTimeField(default=timezone.now)
