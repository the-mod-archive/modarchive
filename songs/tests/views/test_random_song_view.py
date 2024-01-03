from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch

from songs import factories as song_factories

class RandomSongTests(TestCase):
    @patch('songs.views.choice')
    def test_redirects_to_random_song(self, mock_choice):
        # Arrange
        song1 = song_factories.SongFactory()
        song_factories.SongFactory()
        song_factories.SongFactory()
        song_factories.SongFactory()
        mock_choice.return_value = song1.id

        # Act
        response = self.client.get(reverse('random_song'))

        # Assert
        self.assertRedirects(response, reverse('view_song', kwargs = {'pk': song1.id}))
