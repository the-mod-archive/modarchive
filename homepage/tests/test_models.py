from django.test import TestCase
from homepage.tests import factories

class ProfileTests(TestCase):    
    def test_has_comments_is_true_when_profile_has_comments(self):
        profile_1 = factories.UserFactory().profile
        profile_2 = factories.UserFactory().profile
        factories.CommentFactory(profile=profile_1)

        self.assertTrue(profile_1.has_comments())
        self.assertFalse(profile_2.has_comments())