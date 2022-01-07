from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, PasswordChangeView, PasswordResetConfirmView, PasswordResetView, PasswordResetCompleteView
from django.contrib.auth import login
from django.shortcuts import redirect, render
from django.urls import reverse_lazy

from homepage.forms import ChangePasswordForm, ForgotPasswordForm, LoginForm, RegisterUserForm, ResetPasswordForm

class RedirectAuthenticatedUserMixin:
    def dispatch(self, request, *args, **kwargs):
        if (request.user.is_authenticated):
            return redirect("home")
        
        return super().dispatch(request, *args, **kwargs)

def home(request):
    return render(request, 'home_page.html')

@login_required
def profile(request):
    return render(request, 'profile.html')

def register(request):
    # Logged-in users should not be able to view the registration page or submit a request.
    if (request.user.is_authenticated):
        return redirect("home")

    if request.method == 'POST':
        form = RegisterUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user) # TODO: remove this before completion (it should not auto-login when complete)
            return redirect("home")
        else:
            return render(request=request, template_name='register.html', context={"form":form})

    form = RegisterUserForm
    return render(request, 'register.html', context={'form': form})

def password_reset_done(request):
    return render(request, 'password_reset_done.html')

class ModArchiveLoginView(LoginView):
    template_name = 'login.html'
    form_class = LoginForm
    redirect_authenticated_user = True
    
    def get_success_url(self) -> str:
        '''
        Extension of get_success_url to implement remember me. If checkbox is not selected, user gets a normal 
        session id that expires when the browser closes.
        '''
        if not self.request.POST.get('remember_me'):
            self.request.session.set_expiry(0)

        return super().get_success_url()

class ModArchiveChangePasswordView(LoginRequiredMixin, PasswordChangeView):
    template_name = 'change_password.html'
    form_class = ChangePasswordForm
    success_url = reverse_lazy('profile')
    login_url='login'

class ForgotPasswordView(RedirectAuthenticatedUserMixin, PasswordResetView):
    template_name = 'forgot_password.html'
    form_class = ForgotPasswordForm
    email_template_name = 'password_reset_email.html'
    subject_template_name = 'password_reset_email_subject.txt'
    from_email = 'donotreply@modarchive.org'

class CustomPasswordResetConfirmView(RedirectAuthenticatedUserMixin, PasswordResetConfirmView):
    template_name = 'reset_password.html'
    form_class=ResetPasswordForm

class CustomPasswordResetCompleteView(RedirectAuthenticatedUserMixin, PasswordResetCompleteView):
    template_name='password_reset_complete.html'