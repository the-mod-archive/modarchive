from datetime import timedelta
from typing import Any
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models.query import QuerySet
from django.utils import timezone

from homepage.view.common_views import PageNavigationListView
from songs.models import NewSong

class ScreeningIndexView(PermissionRequiredMixin, PageNavigationListView):
    model = NewSong
    template_name="screening.html"
    permission_required = 'songs.can_approve_songs'
    context_object_name = 'new_songs'
    paginate_by = 25
    filter_options = {
        'high_priority': 'High Priority',
        'low_priority': 'Low Priority',
        'by_uploader': 'Uploaded by Artist',
        'my_screening': 'Songs I\'m Screening',
        'others_screening': 'Songs Others are Screening',
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

        # Before doing anything, clear any song claims that are older than 48 hours
        NewSong.objects.filter(claim_date__lte=timezone.now() - timedelta(hours=48)).update(claimed_by=None, claim_date=None)

        # High priority is defined as any song where it's not uploaded by the placeholder account (id of 1)
        if filter_option == 'high_priority':
            queryset = queryset.filter(uploader_profile__user_id__isnull=False).filter(claimed_by=None)
        elif filter_option == 'low_priority':
            queryset = queryset.filter(uploader_profile__user_id=None).filter(claimed_by=None)
        elif filter_option == 'by_uploader':
            queryset = queryset.filter(is_by_uploader=True).filter(claimed_by=None)
        elif filter_option == 'my_screening':
            queryset = queryset.filter(claimed_by=self.request.user.profile)
        elif filter_option == 'others_screening':
            queryset = queryset.exclude(claimed_by=None).exclude(claimed_by=self.request.user.profile)
        else:
            queryset = queryset.filter(claimed_by=None)

        return queryset.order_by('-create_date')
