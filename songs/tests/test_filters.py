from django.http import QueryDict
from django.test import TestCase
from songs.templatetags import filters

class FilterTests(TestCase):
    def test_email_address_filter_masks_single_email_address(self):
        comment = "mod by testguy@test.com which was written in 1996"
        filtered_comment = filters.hide_email_address(comment)
        self.assertEqual("mod by testguy_test.com which was written in 1996", filtered_comment)

    def test_email_address_filter_masks_multiple_email_addresses(self):
        comment = "mod by testguy@test.com and testguy2@test.com which was written in 1996"
        filtered_comment = filters.hide_email_address(comment)
        self.assertEqual(
            "mod by testguy_test.com and testguy2_test.com which was written in 1996"
            , filtered_comment
        )

    def test_email_address_filter_does_not_change_input_without_email_addresses(self):
        comment = "You are listening to a mod by testguy which was written in 1996"
        filtered_comment = filters.hide_email_address(comment)
        self.assertEqual(comment, filtered_comment)

    def test_url_filter_replaces_page_number(self):
        querydict = QueryDict('page=1&filter=all')
        url = filters.url_with_page(querydict, 2)
        self.assertEqual(url, 'page=2&filter=all')

    def test_url_filter_adds_page_number_when_not_originally_present(self):
        querydict = QueryDict('filter=all')
        url = filters.url_with_page(querydict, 2)
        self.assertEqual(url, 'filter=all&page=2')
