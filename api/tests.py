from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from main.models import Paste

User = get_user_model()


class SmokeTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            username="testuser1",
            email="test1@example.com",
            password="testpass123",
            api_key="test_api_key_1",
        )

        self.paste1 = Paste.objects.create(
            id="paste001",
            title="Test Paste 1",
            body="test content 1",
            raw_language="text",
            user=self.user1,
        )

        self.paste2 = Paste.objects.create(
            id="paste002",
            title="Test Paste 2",
            body="test content 2",
            raw_language="text",
            user=self.user1,
        )

        self.paste3 = Paste.objects.create(
            id="paste003",
            title="Test Paste 3",
            body="stuff and things",
            raw_language="text",
            user=self.user1,
        )

    def test_retrieval(self):
        response = self.client.get(
            reverse("api:paste") + "?api_key=" + self.user1.api_key
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["pastes"]), 3)
        self.assertNotIn("body", response.json()["pastes"][0])

        response = self.client.get(
            reverse("api:paste-id", args=[self.paste3.id])
            + "?api_key="
            + self.user1.api_key
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["pastes"]), 1)
        self.assertIn("stuff", response.json()["pastes"][0].get("body", ""))

    def test_posting(self):
        response = self.client.post(
            reverse("api:paste") + "?api_key=" + self.user1.api_key,
            "stuff",
            content_type="application/x-www-form-urlencoded",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["language"], "text")

        paste_id = response.json()["id"]

        response = self.client.get(
            reverse("api:paste-id", args=[paste_id]) + "?api_key=" + self.user1.api_key
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["pastes"]), 1)
        self.assertEqual(response.json()["pastes"][0]["id"], paste_id)

    def test_posting_markdown_source_language(self):
        """The API must accept language=markdown-source without degrading it to autodetect."""
        response = self.client.post(
            reverse("api:paste")
            + "?api_key="
            + self.user1.api_key
            + "&language=markdown-source",
            "# Hello",
            content_type="application/x-www-form-urlencoded",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["language"], "markdown-source")

    def test_authenticated_posting(self):
        response = self.client.post(
            reverse("api:paste") + "?api_key=" + self.user1.api_key,
            "stuff",
            content_type="application/x-www-form-urlencoded",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["language"], "text")

        paste_id = response.json()["id"]
        response = self.client.get(
            reverse("api:paste") + "?api_key=" + self.user1.api_key
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["pastes"]), 4)  # 3 existing + 1 new
        self.assertEqual(response.json()["pastes"][0]["id"], paste_id)

    def test_deletion(self):
        # Create another user to test unauthorized deletion
        other_user = User.objects.create_user(
            username="testuser2",
            email="test2@example.com",
            password="testpass123",
            api_key="test_api_key_2",
        )

        # Test deletion without API key
        response = self.client.delete(reverse("api:paste-id", args=[self.paste1.id]))
        self.assertEqual(response.status_code, 422)

        # Test deletion with wrong user's API key
        response = self.client.delete(
            reverse("api:paste-id", args=[self.paste1.id])
            + "?api_key="
            + other_user.api_key
        )
        self.assertEqual(response.status_code, 422)

        # Test deletion with correct user's API key (should succeed)
        response = self.client.delete(
            reverse("api:paste-id", args=[self.paste1.id])
            + "?api_key="
            + self.user1.api_key
        )
        self.assertEqual(response.status_code, 200)
