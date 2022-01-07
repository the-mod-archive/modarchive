from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm, PasswordResetForm, SetPasswordForm, UsernameField, UserCreationForm
from django.forms.widgets import EmailInput

from homepage.fields import UniqueEmailField

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

class RegisterUserForm(UserCreationForm):
    username = UsernameField(widget=forms.TextInput(attrs={'autofocus': True, 'class': 'input', 'placeholder': 'Username'}))
    email = UniqueEmailField(widget=EmailInput(attrs={'class': 'input', 'placeholder': 'Email Address'}))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'class': 'input', 'placeholder': 'Password'}))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'class': 'input', 'placeholder': 'Repeat Password'}))

    def is_valid(self) -> bool:
        for item in self.errors.as_data().items():
            if item[0] in self.fields:
                self.fields[item[0]].widget.attrs['class'] = 'input is-danger'

        return super().is_valid()

class ForgotPasswordForm(PasswordResetForm):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'autocomplete': 'email', 'class': 'input', 'placeholder': 'Email Address'}))

    def is_valid(self) -> bool:
        for item in self.errors.as_data().items():
            if item[0] in self.fields:
                self.fields[item[0]].widget.attrs['class'] = 'input is-danger'

        return super().is_valid()

class ResetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'class': 'input', 'placeholder': 'New password'}))
    new_password2 = forms.CharField(widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'class': 'input', 'placeholder': 'New password confirmation'}))

    def is_valid(self) -> bool:
        for item in self.errors.as_data().items():
            if item[0] in self.fields:
                self.fields[item[0]].widget.attrs['class'] = 'input is-danger'

        return super().is_valid()