from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm, PasswordResetForm, SetPasswordForm, UsernameField, UserCreationForm
from django.contrib.auth.models import User
from django.forms.widgets import EmailInput
from sceneid.forms import UserCreationForm as BaseUserCreationForm

from homepage.models import Profile
from homepage.fields import BlacklistProtectedEmailField

class LoginForm(AuthenticationForm):
    username = UsernameField(widget=forms.TextInput(attrs={'autofocus': True, 'class': 'form-control', 'placeholder': 'Username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'autocomplete': 'current-password', 'class': 'form-control', 'placeholder': 'Password'}))
    remember_me = forms.BooleanField(required=False, widget=forms.CheckboxInput())

class ChangePasswordForm(PasswordChangeForm):
    old_password = forms.CharField(widget=forms.PasswordInput(attrs={'autocomplete': 'current-password', 'class': 'form-control', 'placeholder': 'Current Password'}))
    new_password1 = forms.CharField(widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'class': 'form-control', 'placeholder': 'New Password'}))
    new_password2 = forms.CharField(widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'class': 'form-control', 'placeholder': 'Repeat New Password'}))

class RegisterUserForm(UserCreationForm):
    username = UsernameField(widget=forms.TextInput(attrs={'autofocus': True, 'class': 'form-control', 'placeholder': 'Username'}))
    email = BlacklistProtectedEmailField(widget=EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'class': 'form-control', 'placeholder': 'Password'}))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'class': 'form-control', 'placeholder': 'Repeat Password'}))

    def save(self, commit=False):
        user = super().save(commit=commit)

        # Test to see if a user already exists with that email address. If so, raise an error
        if User.objects.filter(email=self.cleaned_data['email']).exists():
            raise EmailAddressInUseError("Email address is already in use.")

        user.is_active = False
        user.email = self.cleaned_data['email']

        user.save()
        return user

class ForgotPasswordForm(PasswordResetForm):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'autocomplete': 'email', 'class': 'form-control', 'placeholder': 'Email Address'}))

class ResetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'class': 'form-control', 'placeholder': 'New password'}))
    new_password2 = forms.CharField(widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'class': 'form-control', 'placeholder': 'New password confirmation'}))

class EmailAddressInUseError(Exception):
    pass

class CsvUploadForm(forms.Form):
    csv_file = forms.FileField()

class UpdateProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ("blurb",)

class SceneIDUserCreationForm(BaseUserCreationForm):
    username = UsernameField(widget=forms.TextInput(attrs={'autofocus': True, 'class': 'form-control', 'placeholder': 'Username'}))