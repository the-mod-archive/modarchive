from django.urls import path
from django.views.generic import ListView

from artists.models import Artist
from artists.views import artist

urlpatterns = [
    path('', ListView.as_view(template_name='artist_list.html', model=Artist), {}, 'artists'),
    path('<int:pk>/', artist, {}, 'view_artist')
]