from django.test import TestCase
from songs.templatetags import filters

class FilterTests(TestCase):
    def test_email_address_filter_masks_single_email_address(self):
        comment = "You are listening to a mod by testguy@test.com which was written in 1996"
        filtered_comment = filters.hide_email_address(comment)
        self.assertEqual("You are listening to a mod by testguy_test.com which was written in 1996", filtered_comment)

    def test_email_address_filter_masks_multiple_email_addresses(self):
        comment = "You are listening to a mod by testguy@test.com and testguy2@test.com which was written in 1996"
        filtered_comment = filters.hide_email_address(comment)
        self.assertEqual("You are listening to a mod by testguy_test.com and testguy2_test.com which was written in 1996", filtered_comment)

    def test_email_address_filter_does_not_change_input_without_email_addresses(self):
        comment = "You are listening to a mod by testguy which was written in 1996"
        filtered_comment = filters.hide_email_address(comment)
        self.assertEqual(comment, filtered_comment)
