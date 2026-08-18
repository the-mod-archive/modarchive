from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render
from django.views.generic.base import TemplateView
import logging

from homepage.forms import LoginForm
from homepage.models import News

logger = logging.getLogger(__name__)

class RedirectAuthenticatedUserMixin:
    def dispatch(self, request, *args, **kwargs):
        if (request.user.is_authenticated):
            return redirect("home")
        
        return super().dispatch(request, *args, **kwargs)

class HomePageView(TemplateView):
    template_name='home_page.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['latest_news'] = News.objects.order_by('-id')[:5]
        return context

def page_not_found_view(request, exception):
    return render(request, '404.html')

class LoginView(LoginView):
    template_name = 'account_management/login.html'
    form_class = LoginForm
    redirect_authenticated_user = True

    def form_invalid(self, form):
        logger.warning(
            "Login failed. Username: %r. Errors: %s",
            self.request.POST.get('username'),
            form.errors.as_json(),
        )
        return super().form_invalid(form)
    
    def get_success_url(self) -> str:
        '''
        Extension of get_success_url to implement remember me. If checkbox is not selected, user gets a normal 
        session id that expires when the browser closes.
        '''
        if not self.request.POST.get('remember_me'):
            self.request.session.set_expiry(0)

        return super().get_success_url()