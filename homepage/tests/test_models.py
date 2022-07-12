from django.test import TestCase

from homepage import models

class ProfileTests(TestCase):
    fixtures = ["songs_2.json"]
    
    def test_has_comments_is_true_when_profile_has_comments(self):
        profile = models.Profile.objects.get(id=1)
        self.assertTrue(profile.has_comments())

    def test_has_comments_is_false_when_profile_has_no_comments(self):
        profile = models.Profile.objects.get(id=2)
        self.assertFalse(profile.has_comments())