from django.conf import settings
import requests

def is_recaptcha_success(recaptcha_response):
    if not settings.IS_RECAPTCHA_ENABLED:
        return True

    data = {
        'secret': settings.GOOGLE_RECAPTCHA_SECRET_KEY,
        'response': recaptcha_response
    }
    r = requests.post("https://www.google.com/recaptcha/api/siteverify", data = data)
    result = r.json()

    return result['success']