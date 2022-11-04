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
    minSize = forms.IntegerField(required=False, label="Minimum Size (in bytes)", min_value=0)
    maxSize = forms.IntegerField(required=False, label="Maximum Size (in bytes)", min_value=0)
    minChannels = forms.IntegerField(required=False, label="Minimum number of channels", min_value=1)
    maxChannels = forms.IntegerField(required=False, label="Maximum number of channels", min_value=1)

    def clean(self):
        minSize = self.cleaned_data.get('minSize')
        maxSize = self.cleaned_data.get('maxSize')

        if minSize and maxSize and minSize > maxSize:
            raise forms.ValidationError("Minimum size must be less than or equal to maximum size.")

        minChannels = self.cleaned_data.get('minChannels')
        maxChannels = self.cleaned_data.get('maxChannels')

        if minChannels and maxChannels and minChannels > maxChannels:
            raise forms.ValidationError("Minimum channels must be less than or equal to maximum channels.")

        return super().clean()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        genre_choices_dict = OrderedDict()
        genre_choices_dict["Electronica"] = self.fields['genre'].choices[0:24]
        genre_choices_dict["Demo-style"] = self.fields['genre'].choices[24:27]
        genre_choices_dict["Pop"] = self.fields['genre'].choices[27:37]
        genre_choices_dict["Other"] = self.fields['genre'].choices[37:56]
        genre_choices_dict["Alternative"] = self.fields['genre'].choices[56:62]
        genre_choices_dict["Jazz"] = self.fields['genre'].choices[62:68]
        genre_choices_dict["Hip-Hop"] = self.fields['genre'].choices[68:73]
        genre_choices_dict["Seasonal"] = self.fields['genre'].choices[73:]
        self.fields['genre'].choices = genre_choices_dict.items()