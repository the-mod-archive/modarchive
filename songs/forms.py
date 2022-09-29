from collections import OrderedDict
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django.core.exceptions import ObjectDoesNotExist
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
    def is_valid(self) -> bool:
        for item in self.errors.as_data().items():
            if item[0] in self.fields:
                self.fields[item[0]].widget.attrs['class'] = 'input is-danger'

        return super().is_valid()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['text'].widget.attrs.update({'class': 'form-control'})

    class Meta:
        model = models.ArtistComment
        fields = ("text",)

class SongDetailsForm(ModelForm):
    class Meta:
        model = models.Song
        fields = ("clean_title", "genre")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        genre_choices_dict = OrderedDict()
        genre_choices_dict["None"] = [("", "None")]

        for genre in self.fields['genre'].queryset.order_by('group', 'name'):
            genre_tuple = (genre.id, genre.name)
            try:
                group = genre.group
            except (AttributeError, ObjectDoesNotExist):
                group = False
            
            try:
                genre_choices_dict[group].append(genre_tuple)
            except KeyError:
                genre_choices_dict[group] = [genre_tuple]

        self.fields['genre'].choices = genre_choices_dict.items()