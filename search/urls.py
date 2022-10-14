from django.urls import path

from .views import search, QuickSearchView

urlpatterns = [
    path('', QuickSearchView.as_view(), {}, 'search'),
]