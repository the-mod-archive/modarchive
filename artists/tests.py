from cgitb import html
from django.test import TestCase
from django.urls.base import reverse
from django.contrib.auth.models import User

from artists.forms import CreateArtistForm
from artists.models import Artist
from homepage.models import Profile
from songs.models import Comment

class ArtistViewTests(TestCase):
    fixtures = ["artists.json", "songs.json"]

    def test_artist_list_view_contains_all_artists(self):
        # Arrange
        expected_length = 15
        
        # Act
        response = self.client.get(reverse('artists'))
        
        # Assert
        actual_length = len(response.context['object_list'])
        
        self.assertTemplateUsed(response, 'artist_list.html')
        self.assertTrue('object_list' in response.context)
        self.assertEqual(expected_length, actual_length, f"Expected {expected_length} objects in artists list but got {actual_length}")

    def test_artist_view_contains_specific_artist(self):
        # Act
        response = self.client.get(reverse('view_artist', kwargs = {'pk': 1}))

        # Assert
        self.assertTemplateUsed(response, 'artist.html')
        self.assertTrue('artist' in response.context)

        artist = response.context['artist']
        self.assertEquals('Arcturus', artist.name)
        self.assertEquals(69117, artist.legacy_id)

class AddArtistViewTests(TestCase):
    fixtures = ["users.json"]

    def test_add_artist_rejects_unauthenticated_user(self):
        # Arrange
        add_artist_url = reverse('add_artist')

        # Act
        get_response = self.client.get(reverse('add_artist'))
        post_response = self.client.post(reverse('add_artist'))

        # Assert
        self.assertRedirects(get_response, f'/login/?next={add_artist_url}')
        self.assertRedirects(post_response, f'/login/?next={add_artist_url}')

    def test_add_artist_rejects_user_without_permission(self):
        # Arrange
        self.client.force_login(User.objects.get_or_create(username='test_user')[0])

        # Act
        get_response = self.client.get(reverse('add_artist'))
        post_response = self.client.post(reverse('add_artist'))

        # Assert
        self.assertEqual(403, get_response.status_code)
        self.assertEqual(403, post_response.status_code)

    def test_get_add_artist_renders_correctly_with_permission(self):
        # Arrange
        self.client.force_login(User.objects.get_or_create(username='test_admin')[0])

        # Act
        get_response = self.client.get(reverse('add_artist'))

        # Assert
        self.assertEquals(200, get_response.status_code)
        self.assertTemplateUsed("add_artist.html")

    def test_post_add_artist_creates_an_artist(self):
        # Arrange
        artist_name = 'New Artist'
        self.client.force_login(User.objects.get_or_create(username='test_admin')[0])

        # Act
        response = self.client.post(reverse('add_artist'), {'name': artist_name})

        # Assert
        artist = Artist.objects.latest('create_date')
        self.assertRedirects(response, reverse('view_artist', kwargs = {'pk': artist.id}))
        self.assertEquals(artist_name, artist.name)

    def test_post_add_artist_cannot_create_unnamed_arist(self):
        # Arrange
        self.client.force_login(User.objects.get_or_create(username='test_admin')[0])

        # Act
        response = self.client.post(reverse('add_artist'), {'name': ''})

        # Assert
        self.assertEquals("This field is required.", response.context['form'].errors['name'][0])

    def test_post_add_artist_cannot_create_artist_with_identical_name(self):
        # Arrange
        Artist.objects.create(name="New Artist")
        self.client.force_login(User.objects.get_or_create(username='test_admin')[0])

        # Act
        response = self.client.post(reverse('add_artist'), {'name': 'New Artist'})

        # Assert
        self.assertEquals("Artist with this Name already exists.", response.context['form'].errors['name'][0])

    def test_post_add_artist_cannot_create_artist_with_identical_name_case_insensitive(self):
        # Arrange
        Artist.objects.create(name="New Artist")
        self.client.force_login(User.objects.get_or_create(username='test_admin')[0])

        # Act
        response = self.client.post(reverse('add_artist'), {'name': 'new artist'})

        # Assert
        self.assertEquals("Artist with this Name already exists.", response.context['form'].errors['name'][0])

class CreateArtistFormTests(TestCase):
    fixtures = ["songs.json", "artists.json"]

    def test_form_is_not_valid_when_artist_name_is_blank(self):
        form = CreateArtistForm(data={})

        self.assertFalse(form.is_valid())

    def test_form_is_not_valid_when_artist_name_is_not_unique(self):
        form = CreateArtistForm(data={"name": "Arcturus"})

        self.assertFalse(form.is_valid())

    def test_form_is_valid_when_artist_name_is_unique(self):
        form = CreateArtistForm(data={"name": "New Unique Name"})

        self.assertTrue(form.is_valid())

    def test_form_is_not_valid_when_artist_name_is_not_unique_case_insensitive(self):
        form = CreateArtistForm(data={"name": "arcturuS"})

        self.assertFalse(form.is_valid())