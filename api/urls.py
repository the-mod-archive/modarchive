from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SongViewSet, ArtistViewSet, SongSearchAPIView, SongDownloadView, GenreListAPIView, ArtistSearchAPIView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

router = DefaultRouter()
router.register(r'songs', SongViewSet)
router.register(r'artists', ArtistViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('songs/search', SongSearchAPIView.as_view()),
    path('genres', GenreListAPIView.as_view()),
    path('artists/search', ArtistSearchAPIView.as_view()),
    path('download/<int:pk>', SongDownloadView.as_view(), name='song_download'),
    path('schema', SpectacularAPIView.as_view(), name='schema'),
    path('swagger',  SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
