from django import forms

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit

from interactions import models

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
