from django.test import TestCase, override_settings
from django.core.urlresolvers import reverse


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class SmokeTests(TestCase):
    def test_urls(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
