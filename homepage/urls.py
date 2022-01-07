from django.urls.conf import re_path

from django.contrib.auth import views as auth_views
from django.urls.conf import re_path
from django.urls import path
from homepage.views import ForgotPasswordView, ModArchiveChangePasswordView, CustomPasswordResetConfirmView, CustomPasswordResetCompleteView, home, ModArchiveLoginView, password_reset_done, profile, register

urlpatterns = [
    # Basic homepage
    re_path(r'^$', home, {}, 'home'),
    re_path(r'^profile/$', profile, {}, 'profile'),

    # Security and Authentication
    re_path(r'^login/$', ModArchiveLoginView.as_view(), name='login', kwargs={'next': '/'}),
    re_path(r'logout/$', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    re_path(r'change_password/$', ModArchiveChangePasswordView.as_view(), name='change_password'),
    re_path(r'register/$', register, {}, 'register'),
    re_path(r'forgot_password/$', ForgotPasswordView.as_view(), {}, 'forgot_password'),
    re_path(r'password_reset_done/$', password_reset_done, {}, 'password_reset_done'),
    path('password_reset/<uidb64>/<token>/', CustomPasswordResetConfirmView.as_view(), name='password_reset'),
    path('password_reset_complete/', CustomPasswordResetCompleteView.as_view(), name='password_reset_complete')
]