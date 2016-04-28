from django.test import TestCase, override_settings
from django.core.urlresolvers import reverse


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class SmokeTests(TestCase):
    def test_urls(self):
        response = self.client.post(reverse("api:paste"), "stuff", content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code, 200)
