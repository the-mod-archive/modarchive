from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SongViewSet, ArtistViewSet, SongSearchAPIView, SongDownloadView

router = DefaultRouter()
router.register(r'songs', SongViewSet)
router.register(r'artists', ArtistViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('search', SongSearchAPIView.as_view()),
    path('download/<int:pk>', SongDownloadView.as_view(), name='song_download'),
]
