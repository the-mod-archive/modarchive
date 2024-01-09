from typing import Any
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models.query import QuerySet

from homepage.view.common_views import PageNavigationListView
from songs.models import NewSong

class ScreeningView(PermissionRequiredMixin, PageNavigationListView):
    model = NewSong
    template_name="screening.html"
    permission_required = 'songs.can_approve_songs'
    context_object_name = 'new_songs'
    paginate_by = 40
    filter_options = {
        'high_priority': 'High Priority',
        'low_priority': 'Low Priority',
        'by_uploader': 'Uploaded by Artist',
        'all': 'All'
    }

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['filter_options'] = self.filter_options
        context['filter'] = self.request.GET.get('filter', 'all')
        return context

    def get_queryset(self) -> QuerySet[Any]:
        queryset = super().get_queryset()

        # Get filter option from request
        filter_option = self.request.GET.get('filter', 'all')

        if filter_option not in self.filter_options:
            filter_option = 'all'

        # High priority is defined as any song where it's not uploaded by the placeholder account (id of 1)
        if filter_option == 'high_priority':
            queryset = queryset.filter(uploader_profile__user_id__gt=1)
        elif filter_option == 'low_priority':
            queryset = queryset.filter(uploader_profile__user_id=None)
        elif filter_option == 'by_uploader':
            queryset = queryset.filter(is_by_uploader=True)

        return queryset
