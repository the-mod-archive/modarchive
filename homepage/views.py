from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView, PasswordChangeView, PasswordResetConfirmView, PasswordResetView, PasswordResetCompleteView
from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views.generic.base import TemplateView, RedirectView

from homepage.forms import ChangePasswordForm, EmailAddressInUseError, ForgotPasswordForm, LoginForm, RegisterUserForm, ResetPasswordForm
from homepage.tokens import account_activation_token

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
            try:
                user = form.save()
                subject = "Active your ModArchive account"

                message = render_to_string('account_activation_email.html', {
                    'user': user,
                    'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                    'token': account_activation_token.make_token(user),
                    'domain': get_current_site(request).domain
                })

                user.email_user(subject, message, 'donotreply@modarchive.org')
                return redirect("register_done")

            except EmailAddressInUseError:
                user = User.objects.get(email = form.cleaned_data['email'])
                subject = "ModArchive security warning"
                message = "A user attempted to register a ModArchive account with your email address."
                user.email_user(subject, message, 'donotreply@modarchive.org')
                return redirect("register_done")
            
        else:
            return render(request=request, template_name='register.html', context={"form":form})

    form = RegisterUserForm
    return render(request, 'register.html', context={'form': form})

def password_reset_done(request):
    return render(request, 'password_reset_done.html')

class CustomLoginView(LoginView):
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

class CustomPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    template_name = 'change_password.html'
    form_class = ChangePasswordForm
    success_url = reverse_lazy('profile')
    login_url='login'

class CustomPasswordResetview(RedirectAuthenticatedUserMixin, PasswordResetView):
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

class AccountActivationCompleteView(RedirectAuthenticatedUserMixin, TemplateView):
    template_name = 'account_activation_complete.html'

def activate(request, uidb64, token):
    if (request.user.is_authenticated):
        return redirect("home")

    User = get_user_model()
    try:  
        uid = force_str(urlsafe_base64_decode(uidb64))  
        user = User.objects.get(pk=uid)  
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    if user is None:
        return redirect('activation_error')
    elif user.is_active:
        # Take no action if user is already active
        return redirect('home')
    
    user.is_active = True
    user.save()
    return redirect('account_activation_complete')

class LegacyUrlRedirectionView(RedirectView):
    redirection_map = {
        'login': {
            'log_in': 'login'
        },
        'assistance': {
            'create_account_page': 'register',
            'forgot_password_page': 'forgot_password'
        },
        'interactive': {
            'change_password_page': 'change_password'
        },
        'default': {
            'default': 'home'
        }
    }

    def get_redirect_url(self, *args, **kwargs):
        php_reference = kwargs.get('php_file', 'default')
        param = self.request.GET.get('request', 'default').lower()
        return reverse(self.redirection_map.get(php_reference).get(param, 'home'))