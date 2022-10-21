from django import forms

class SearchForm(forms.Form):
    query = forms.CharField(label=False)
    songs = forms.BooleanField(required=False, initial=True)
    artists = forms.BooleanField(required=False, initial=True)