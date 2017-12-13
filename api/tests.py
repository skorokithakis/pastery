from django.urls import reverse
from django.test import TestCase

from main.tests import PasteFactory, UserFactory


class SmokeTests(TestCase):
    def setUp(self):
        self.user1 = UserFactory.example()
        self.paste1 = PasteFactory.example()
        self.paste2 = PasteFactory.example()
        self.paste3 = PasteFactory.example()

        self.paste3.user = self.user1
        self.paste3.body = "stuff and things"
        self.paste3.save()

    def test_retrieval(self):
        response = self.client.get(reverse("api:paste") + "?api_key=" + self.user1.api_key)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["pastes"]), 1)
        self.assertNotIn("body", response.json()["pastes"][0])

        response = self.client.get(reverse("api:paste-id", args=[self.paste3.id]) + "?api_key=" + self.user1.api_key)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["pastes"]), 1)
        self.assertIn("stuff", response.json()["pastes"][0].get("body", ""))

    def test_posting(self):
        response = self.client.post(reverse("api:paste"), "stuff", content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["language"], "text")

        paste_id = response.json()["id"]

        response = self.client.get(reverse("api:paste-id", args=[paste_id]) + "?api_key=" + self.user1.api_key)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["pastes"]), 1)
        self.assertEqual(response.json()["pastes"][0]["id"], paste_id)

    def test_authenticated_posting(self):
        response = self.client.post(reverse("api:paste") + "?api_key=" + self.user1.api_key, "stuff", content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["language"], "text")

        paste_id = response.json()["id"]
        response = self.client.get(reverse("api:paste") + "?api_key=" + self.user1.api_key)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["pastes"]), 2)
        self.assertEqual(response.json()["pastes"][0]["id"], paste_id)

    def test_deletion(self):
        response = self.client.delete(reverse("api:paste-id", args=[self.paste1.id]))
        self.assertEqual(response.status_code, 422)

        response = self.client.delete(reverse("api:paste-id", args=[self.paste1.id]) + "?api_key=" + self.user1.api_key)
        self.assertEqual(response.status_code, 422)

        self.paste1.user = self.user1
        self.paste1.save()

        response = self.client.delete(reverse("api:paste-id", args=[self.paste1.id]) + "?api_key=" + self.user1.api_key)
        self.assertEqual(response.status_code, 200)
