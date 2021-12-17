from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm, UsernameField

class LoginForm(AuthenticationForm):
    username = UsernameField(widget=forms.TextInput(attrs={'autofocus': True, 'class': 'input', 'placeholder': 'Username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'autocomplete': 'current-password', 'class': 'input', 'placeholder': 'Password'}))
    remember_me = forms.BooleanField(required=False, widget=forms.CheckboxInput())

    def is_valid(self) -> bool:
        for item in self.errors.as_data().items():
            if item[0] in self.fields:
                self.fields[item[0]].widget.attrs['class'] = 'input is-danger'

        return super().is_valid()

class ChangePasswordForm(PasswordChangeForm):
    old_password = forms.CharField(widget=forms.PasswordInput(attrs={'autocomplete': 'current-password', 'class': 'input', 'placeholder': 'Current Password'}))
    new_password1 = forms.CharField(widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'class': 'input', 'placeholder': 'New Password'}))
    new_password2 = forms.CharField(widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'class': 'input', 'placeholder': 'Repeat New Password'}))