from django.urls import path
from django.views.generic.base import TemplateView

urlpatterns = [
    path('', TemplateView.as_view(template_name='index.html'), {}, 'songs'),
    path('<int:id>/', TemplateView.as_view(template_name='song.html'), {}, 'view_song')
]