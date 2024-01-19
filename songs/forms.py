from collections import OrderedDict
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django import forms

from songs import models
from songs import constants

class AdminSongForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(AdminSongForm, self).__init__(*args, **kwargs)
        self.fields['comment_text'].strip = False
        self.fields['instrument_text'].strip = False

    class Meta:
        model = models.Song
        fields = (
            'legacy_id',
            'filename',
            'filename_unzipped',
            'title',
            'clean_title',
            'format',
            'file_size',
            'channels',
            'comment_text',
            'instrument_text',
            'hash',
            'pattern_hash',
            'license',
            'genre',
            'folder',
            'is_featured',
            'featured_date',
            'featured_by'
        )

class AddCommentForm(forms.ModelForm):
    def is_valid(self) -> bool:
        for item in self.errors.as_data().items():
            if item[0] in self.fields:
                self.fields[item[0]].widget.attrs['class'] = 'input is-danger'

        return super().is_valid()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['rating'].widget.attrs.update({'class': 'form-select'})
        self.fields['text'].widget.attrs.update({'class': 'form-control'})

        self.helper = FormHelper()
        self.helper.form_id = 'id-add-comment-form'
        self.helper.form_method = 'post'

        self.helper.add_input(Submit('submit', 'Submit'))

    class Meta:
        model = models.Comment
        fields = ("rating", "text")

class AddArtistCommentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['text'].required = False
        self.fields['text'].label = "Comment Text"
        self.fields['text'].help_text = "Optional commentary for your own song. Limit 5000 characters."

    class Meta:
        model = models.ArtistComment
        fields = ("text",)

class GenreMixin(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        genre_choices_dict = OrderedDict()
        genre_choices_dict["None"] = [("", "None")]
        genre_choices_dict["Electronica"] = self.fields['genre'].choices[1:25]
        genre_choices_dict["Demo-style"] = self.fields['genre'].choices[25:28]
        genre_choices_dict["Pop"] = self.fields['genre'].choices[28:38]
        genre_choices_dict["Other"] = self.fields['genre'].choices[38:58]
        genre_choices_dict["Alternative"] = self.fields['genre'].choices[58:64]
        genre_choices_dict["Jazz"] = self.fields['genre'].choices[64:70]
        genre_choices_dict["Hip-Hop"] = self.fields['genre'].choices[70:75]
        genre_choices_dict["Seasonal"] = self.fields['genre'].choices[75:]

        self.fields['genre'].choices = genre_choices_dict.items()

class SongGenreForm(GenreMixin, forms.ModelForm):
    class Meta:
        model = models.Song
        fields = ("genre",)

class SongDetailsForm(GenreMixin, forms.ModelForm):
    class Meta:
        model = models.Song
        fields = ("clean_title", "genre")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['clean_title'].help_text = '''
        Cleaned up version of title for display and search purposes. Use this to remove unwanted characters, artist name, etc. Does not change the title in the file itself.
        If left blank, the original title will display instead.
        '''

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
            )
        ),
        (constants.CLAIMED_GROUP, (
            (constants.MY_SCREENING_FILTER, constants.MY_SCREENING_FILTER_DESCRIPTION),
            (constants.OTHERS_SCREENING_FILTER, constants.OTHERS_SCREENING_FILTER_DESCRIPTION),
            )
        ),
        (constants.DONE_GROUP, (
            (constants.PRE_SCREENED_FILTER, constants.PRE_SCREENED_FILTER_DESCRIPTION),
            (constants.PRE_SCREENED_AND_RECOMMENDED_FILTER, constants.PRE_SCREENED_AND_RECOMMENDED_FILTER_DESCRIPTION),
            )
        ),
        (constants.FLAGGED_GROUP, (
            (constants.NEEDS_SECOND_OPINION_FILTER, constants.NEEDS_SECOND_OPINION_FILTER_DESCRIPTION),
            (constants.POSSIBLE_DUPLICATE_FILTER, constants.POSSIBLE_DUPLICATE_FILTER_DESCRIPTION),
            (constants.UNDER_INVESTIGATION_FILTER, constants.UNDER_INVESTIGATION_FILTER_DESCRIPTION),
            )
        )
    )

    filter = forms.ChoiceField(choices=FILTER_CHOICES, required=False, widget=forms.Select(attrs={'id': 'filterDropdown'}))

    class Meta:
        required_css_class = None
