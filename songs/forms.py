from collections import OrderedDict
from django import forms

from songs import models

class MergeSongForm(forms.Form):
    song_to_merge_into_id = forms.IntegerField(label='Song ID to Merge Into')
    commit = forms.BooleanField(initial=False, widget=forms.HiddenInput(), required=False)

class CommitMergeSongForm(forms.Form):
    commit = forms.BooleanField(initial=True, widget=forms.HiddenInput(), required=True)
    song_to_merge_into_id = forms.IntegerField(widget=forms.HiddenInput(), required=True)

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
        fields = ("title", "genre")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].help_text = '''
        Clean title for search and display purposes. Use this to remove unwanted characters, artist name, etc. Does not change the title in the file itself.
        If not sure what to set this to, use the filename.
        '''
