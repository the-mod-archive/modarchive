from django.contrib.auth import views as auth_views
from django.urls import path, re_path
from django.views.generic.base import TemplateView
from homepage.views import AccountActivationCompleteView, CustomPasswordResetview, CustomPasswordChangeView, CustomPasswordResetConfirmView, CustomPasswordResetCompleteView, LegacyUrlRedirectionView, activate, home, CustomLoginView, password_reset_done, profile, register

urlpatterns = [
    # Basic homepage
    path('', home, {}, 'home'),
    path('profile/', profile, {}, 'profile'),

    # Basic auth functionality
    path('login/', CustomLoginView.as_view(), name='login', kwargs={'next': '/'}),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('change_password/', CustomPasswordChangeView.as_view(), name='change_password'),
    
    # Account registration
    path('register/', register, {}, 'register'),
    path('register_done/', TemplateView.as_view(template_name='registration/register_done.html'), {}, 'register_done'),
    path('activate_account/<uidb64>/<token>', activate, name='activate_account'),
    path('account_activation_complete/', AccountActivationCompleteView.as_view(), {}, 'account_activation_complete'),
    path('activation_error/', TemplateView.as_view(template_name='registration/account_activation_error.html'), {}, 'activation_error'),
    
    # Password reset
    path('forgot_password/', CustomPasswordResetview.as_view(), {}, 'forgot_password'),
    path('password_reset_done/', password_reset_done, {}, 'password_reset_done'),
    path('password_reset/<uidb64>/<token>/', CustomPasswordResetConfirmView.as_view(), name='password_reset'),
    path('password_reset_complete/', CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),

    # Legacy URL redirects
    re_path('(?P<php_file>[a-zA-Z]+).php/', LegacyUrlRedirectionView.as_view(), name='login_php'),
]