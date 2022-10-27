from django.urls import path

from .views import QuickSearchView, AdvancedSearchView

urlpatterns = [
    path('', QuickSearchView.as_view(), {}, 'search'),
    path('advanced', AdvancedSearchView.as_view(), {}, 'advanced_search')
]