from django.test import TestCase
from django.core.urlresolvers import reverse

from main.tests import PasteFactory, UserFactory


class SmokeTests(TestCase):
    def setUp(self):
        self.user1 = UserFactory.example()
        self.paste1 = PasteFactory.example()
        self.paste2 = PasteFactory.example()

    def test_retrieval(self):
        response = self.client.get(reverse("api:paste-id", args=[self.paste1.id]) + "?api_key=" + self.user1.api_key)
        self.assertEqual(response.status_code, 200)

    def test_posting(self):
        response = self.client.post(reverse("api:paste"), "stuff", content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["language"], "text")

        paste_id = response.json()["id"]
        response = self.client.get(reverse("api:paste-id", args=[paste_id]) + "?api_key=" + self.user1.api_key)
        self.assertEqual(response.status_code, 200)

    def test_deletion(self):
        response = self.client.delete(reverse("api:paste-id", args=[self.paste1.id]))
        self.assertEqual(response.status_code, 422)

        response = self.client.delete(reverse("api:paste-id", args=[self.paste1.id]) + "?api_key=" + self.user1.api_key)
        self.assertEqual(response.status_code, 200)
