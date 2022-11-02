from collections import OrderedDict
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django.forms import ModelForm

from songs import models

class AdminSongForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(AdminSongForm, self).__init__(*args, **kwargs)
        self.fields['comment_text'].strip = False
        self.fields['instrument_text'].strip = False

    class Meta:
        model = models.Song
        fields = "__all__"

class AddCommentForm(ModelForm):
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

class AddArtistCommentForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['text'].required = False
        self.fields['text'].label = "Comment Text"
        self.fields['text'].help_text = "Optional commentary for your own song. Limit 5000 characters."

    class Meta:
        model = models.ArtistComment
        fields = ("text",)

class GenreMixin(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        genre_choices_dict = OrderedDict()
        genre_choices_dict["None"] = [("", "None")]
        genre_choices_dict["Electronica"] = self.fields['genre'].choices[1:25]
        genre_choices_dict["Demo-style"] = self.fields['genre'].choices[25:28]
        genre_choices_dict["Pop"] = self.fields['genre'].choices[28:38]
        genre_choices_dict["Other"] = self.fields['genre'].choices[38:57]
        genre_choices_dict["Alternative"] = self.fields['genre'].choices[57:63]
        genre_choices_dict["Jazz"] = self.fields['genre'].choices[63:69]
        genre_choices_dict["Hip-Hop"] = self.fields['genre'].choices[69:74]
        genre_choices_dict["Seasonal"] = self.fields['genre'].choices[74:]

        self.fields['genre'].choices = genre_choices_dict.items()

class SongGenreForm(GenreMixin, ModelForm):
    class Meta:
        model = models.Song
        fields = ("genre",)

class SongDetailsForm(GenreMixin, ModelForm):
    class Meta:
        model = models.Song
        fields = ("clean_title", "genre")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['clean_title'].help_text = '''
        Cleaned up version of title for display and search purposes. Use this to remove unwanted characters, artist name, etc. Does not change the title in the file itself.
        If left blank, the original title will display instead.
        '''