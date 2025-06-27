from django.urls import path

from interactions.views.add_favorite_view import AddFavoriteView
from interactions.views.remove_favorite_view import RemoveFavoriteView
from interactions.views.comment_view import CommentView

urlpatterns = [
    path('<int:pk>/add_favorite', AddFavoriteView.as_view(), {}, 'add_favorite'),
    path('<int:pk>/remove_favorite', RemoveFavoriteView.as_view(), {}, 'remove_favorite'),
    path('<int:pk>/comment', CommentView.as_view(), {}, 'add_comment'),
]
