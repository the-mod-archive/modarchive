from django import forms
from songs import models

class SearchForm(forms.Form):
    query = forms.CharField(label=False)
    songs = forms.BooleanField(required=False, initial=True)
    artists = forms.BooleanField(required=False, initial=True)

class AdvancedSearchForm(forms.Form):
    query = forms.CharField(label=False)
    format = forms.MultipleChoiceField(required=False, choices=models.Song.Formats.choices)
    license = forms.MultipleChoiceField(required=False, choices=models.Song.Licenses.choices)