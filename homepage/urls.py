from django.http import request
from django.urls.conf import re_path

from django.contrib.auth import views as auth_views
from django.urls.conf import re_path
from homepage.views import ModArchiveChangePasswordView, home, ModArchiveLoginView, profile, register

urlpatterns = [
    # Basic homepage
    re_path(r'^$', home, {}, 'home'),
    re_path(r'^profile/$', profile, {}, 'profile'),

    # Security and Authentication
    re_path(r'^login/$', ModArchiveLoginView.as_view(), name='login', kwargs={'next': '/'}),
    re_path(r'logout/$', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    re_path(r'change_password/$', ModArchiveChangePasswordView.as_view(), name='change_password'),
    re_path(r'register/$', register, {}, 'register')
]