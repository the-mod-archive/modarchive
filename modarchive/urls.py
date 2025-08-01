"""modarchive URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls.conf import include, re_path
from django.urls import path

urlpatterns = [
    re_path(r'^admin/', admin.site.urls),
    re_path(r'^', include('homepage.urls')),
    path('songs/', include('songs.urls')),
    path('api/v1/', include('api.urls')),
    path('artists/', include('artists.urls')),
    path('search/', include('search.urls')),
    path('uploads/', include('uploads.urls')),
    path('interactions/', include('interactions.urls')),
    # path('account/sceneid/', include('sceneid.urls')),
]