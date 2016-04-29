from django.test import TestCase
from django.core.urlresolvers import reverse


class SmokeTests(TestCase):
    def test_urls(self):
        response = self.client.post(reverse("api:paste"), "stuff", content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["language"], "text")

        paste_id = response.json()["id"]
        response = self.client.get(reverse("api:paste-id", args=[paste_id]))
        self.assertEqual(response.status_code, 422)
