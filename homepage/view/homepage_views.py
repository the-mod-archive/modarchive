from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render

from homepage.forms import LoginForm

class RedirectAuthenticatedUserMixin:
    def dispatch(self, request, *args, **kwargs):
        if (request.user.is_authenticated):
            return redirect("home")
        
        return super().dispatch(request, *args, **kwargs)

def home(request):
    return render(request, 'home_page.html')

def page_not_found_view(request, exception):
    return render(request, '404.html')

@login_required
def account_settings(request):
    return render(request, 'account_management/account_settings.html')

class LoginView(LoginView):
    template_name = 'account_management/login.html'
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