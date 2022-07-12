from django.test import TestCase
from django.urls.base import reverse

from artists.models import Artist

# Create your tests here.
class SearchViewTests(TestCase):
    fixtures = ['songs.json', 'artists.json']

    def test_basic_search_yields_results(self):
        # Arrange
        artists = Artist.objects.all()
        for artist in artists:
            artist.save()

        response = self.client.get('/search/?q=necros')

        self.assertTemplateUsed("search_results.html")
        self.assertTrue('search_results' in response.context)