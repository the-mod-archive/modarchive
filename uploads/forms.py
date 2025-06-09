import re
import os
from django import forms

from . import constants, models

class UploadForm(forms.Form):
    CHOICES = (
        ('yes', 'Yes. Selecting this option will also ensure your material is added to your artist profile after passing screening.'),
        ('no', 'No. I am uploading material I understand to be in the Public Domain, or have acquired permission from the author to upload the material here.'),
    )
    written_by_me = forms.ChoiceField(choices=CHOICES, widget=forms.RadioSelect(), required=True, label='Is this material your own work to which you own the copyright?')
    song_file = forms.FileField(required=True)

    class Meta:
        required_css_class = None

class ScreeningQueueFilterForm(forms.Form):
    FILTER_CHOICES = (
        (constants.UNCLAIMED_GROUP, (
            (constants.HIGH_PRIORITY_FILTER, constants.HIGH_PRIORITY_FILTER_DESCRIPTION),
            (constants.LOW_PRIORITY_FILTER, constants.LOW_PRIORITY_FILTER_DESCRIPTION),
            (constants.BY_UPLOADER_FILTER, constants.BY_UPLOADER_FILTER_DESCRIPTION),
            (constants.NEEDS_SECOND_OPINION_FILTER, constants.NEEDS_SECOND_OPINION_FILTER_DESCRIPTION),
            (constants.POSSIBLE_DUPLICATE_FILTER, constants.POSSIBLE_DUPLICATE_FILTER_DESCRIPTION),
            (constants.UNDER_INVESTIGATION_FILTER, constants.UNDER_INVESTIGATION_FILTER_DESCRIPTION),
            )
        ),
        (constants.YOUR_REVIEW_GROUP, (
            (constants.MY_SCREENING_FILTER, constants.MY_SCREENING_FILTER_DESCRIPTION),
            )
        ),
        (constants.NOT_YOUR_REVIEW_GROUP, (
            (constants.OTHERS_SCREENING_FILTER, constants.OTHERS_SCREENING_FILTER_DESCRIPTION),
        )
        ),
        (constants.READY_TO_BE_ADDED_GROUP, (
            (constants.PRE_SCREENED_FILTER, constants.PRE_SCREENED_FILTER_DESCRIPTION),
            (constants.PRE_SCREENED_AND_RECOMMENDED_FILTER, constants.PRE_SCREENED_AND_RECOMMENDED_FILTER_DESCRIPTION),
            )
        )
    )

    filter = forms.ChoiceField(choices=FILTER_CHOICES, required=False, widget=forms.Select(attrs={'id': 'filterDropdown'}))

    class Meta:
        required_css_class = None

class RejectionForm(forms.Form):
    is_temporary = forms.BooleanField(required=False, label='Temporary rejection?', widget=forms.CheckboxInput())
    rejection_reason = forms.ChoiceField(choices=models.RejectedSong.Reasons.choices, required=True, label='Rejection reason')
    message = forms.CharField(required=False,
        label='Message (optional)',
        widget=forms.Textarea(attrs={'rows': 4, 'cols': 40}),
        max_length=1000,
        help_text='Optional message to the uploader. If you do not enter a message, the uploader will see a default message for the rejection reason instead. Limit 1000 characters.'
    )

    class Meta:
        required_css_class = None

class RenameForm(forms.ModelForm):
    new_filename = forms.CharField(required=True, label='New filename', max_length=59, help_text='The new filename for the song. Do not change the file extension.')

    class Meta:
        model = models.NewSong
        fields = ('new_filename',)
        required_css_class = None

    def clean_new_filename(self):
        new_filename = self.cleaned_data['new_filename']

        # Validate that filename has changed
        if new_filename.lower() == self.instance.filename.lower():
            raise forms.ValidationError(constants.RENAME_MUST_BE_CHANGED)

        # Validate that filename adheres to Unix filename conventions
        if not re.match(r'^[a-zA-Z0-9._-]+$', new_filename):
            raise forms.ValidationError(constants.RENAME_INVALID_FILENAME)

        current_format = self.instance.format
        _, extension = os.path.splitext(new_filename)

        # Validate that file extension has not changed
        if extension.lower() != f'.{current_format.lower()}':
            raise forms.ValidationError(constants.RENAME_CANNOT_CHANGE_FILE_EXTENSION)

        # Validate that filename is not already taken
        if self.filename_not_unique(new_filename):
            raise forms.ValidationError(constants.RENAME_FILENAME_TAKEN)

        return new_filename

    def filename_not_unique(self, new_filename):
        return (models.NewSong.objects.filter(filename=new_filename).exists() or
            models.Song.objects.filter(filename=new_filename).exists() or
            models.RejectedSong.objects.filter(filename=new_filename).exists()
        )