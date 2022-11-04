from collections import OrderedDict
from django import forms
from songs import models

class SearchForm(forms.Form):
    query = forms.CharField(label=False)
    songs = forms.BooleanField(required=False, initial=True)
    artists = forms.BooleanField(required=False, initial=True)

class AdvancedSearchForm(forms.Form):
    query = forms.CharField(label=False)
    format = forms.MultipleChoiceField(required=False, choices=models.Song.Formats.choices)
    genre = forms.MultipleChoiceField(required=False, choices=models.Song.Genres.choices)
    license = forms.MultipleChoiceField(required=False, choices=models.Song.Licenses.choices)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        genre_choices_dict = OrderedDict()
        genre_choices_dict["None"] = [("", "None")]
        genre_choices_dict["Electronica"] = self.fields['genre'].choices[0:24]
        genre_choices_dict["Demo-style"] = self.fields['genre'].choices[24:27]
        genre_choices_dict["Pop"] = self.fields['genre'].choices[27:37]
        genre_choices_dict["Other"] = self.fields['genre'].choices[37:56]
        genre_choices_dict["Alternative"] = self.fields['genre'].choices[56:62]
        genre_choices_dict["Jazz"] = self.fields['genre'].choices[62:68]
        genre_choices_dict["Hip-Hop"] = self.fields['genre'].choices[68:73]
        genre_choices_dict["Seasonal"] = self.fields['genre'].choices[73:]
        self.fields['genre'].choices = genre_choices_dict.items()