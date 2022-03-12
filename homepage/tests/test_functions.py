from unittest.mock import patch
from django.test import TestCase

from homepage.functions import is_recaptcha_success

class RecaptchaTests(TestCase):
    class DummyResponse:
        def __init__(self, expected_success_value = True) -> None:
            self.success = expected_success_value
            
        def json(self):
            return { 'success': self.success }

    def test_returns_true_if_captcha_is_disabled(self):
        with self.settings(IS_RECAPTCHA_ENABLED = False):
            self.assertTrue(is_recaptcha_success(None))

    @patch("homepage.functions.requests.post")
    def test_returns_true_if_captcha_succeeds(self, mock_post):
        mock_post.return_value = self.DummyResponse()
        with self.settings(IS_RECAPTCHA_ENABLED = True):
            self.assertTrue(is_recaptcha_success(None))

    @patch("homepage.functions.requests.post")
    def test_returns_false_if_captcha_fails(self, mock_post):
        mock_post.return_value = self.DummyResponse(False)
        with self.settings(IS_RECAPTCHA_ENABLED = True):
            self.assertFalse(is_recaptcha_success(None))