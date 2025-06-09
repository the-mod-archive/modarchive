from collections import OrderedDict
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django import forms

from songs import models

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

class MergeSongForm(forms.Form):
    song_to_merge_into_id = forms.IntegerField(label='Song ID to Merge Into')
    commit = forms.BooleanField(initial=False, widget=forms.HiddenInput(), required=False)

class CommitMergeSongForm(forms.Form):
    commit = forms.BooleanField(initial=True, widget=forms.HiddenInput(), required=True)
    song_to_merge_into_id = forms.IntegerField(widget=forms.HiddenInput(), required=True)

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
        genre_choices_dict["Electronica"] = list(self.fields['genre'].choices)[1:25]
        genre_choices_dict["Demo-style"] = list(self.fields['genre'].choices)[25:28]
        genre_choices_dict["Pop"] = list(self.fields['genre'].choices)[28:38]
        genre_choices_dict["Other"] = list(self.fields['genre'].choices)[38:58]
        genre_choices_dict["Alternative"] = list(self.fields['genre'].choices)[58:64]
        genre_choices_dict["Jazz"] = list(self.fields['genre'].choices)[64:70]
        genre_choices_dict["Hip-Hop"] = list(self.fields['genre'].choices)[70:75]
        genre_choices_dict["Seasonal"] = list(self.fields['genre'].choices)[75:]

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
