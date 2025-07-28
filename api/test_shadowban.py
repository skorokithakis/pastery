from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from main.models import Paste

User = get_user_model()


class ShadowbanTests(TestCase):
    def setUp(self):
        # Create users without using factories to avoid Hypothesis issues
        self.normal_user = User.objects.create_user(
            username="normal_user",
            email="normal@example.com",
            password="testpass123",
            api_key="normal_api_key",
        )

        self.shadowbanned_user = User.objects.create_user(
            username="shadowbanned_user",
            email="shadowbanned@example.com",
            password="testpass123",
            api_key="shadowbanned_api_key",
            shadowbanned=True,
        )

        self.other_user = User.objects.create_user(
            username="other_user",
            email="other@example.com",
            password="testpass123",
            api_key="other_api_key",
        )

        # Create pastes from both users
        self.normal_paste = Paste.objects.create(
            id="normal123",
            title="Normal Paste",
            body="This is a normal paste",
            raw_language="text",
            user=self.normal_user,
        )

        self.shadowbanned_paste = Paste.objects.create(
            id="shadow123",
            title="Shadowbanned Paste",
            body="This is a shadowbanned paste",
            raw_language="text",
            user=self.shadowbanned_user,
        )

    def test_shadowbanned_user_can_see_own_paste(self):
        """Shadowbanned user should be able to see their own paste via API."""
        response = self.client.get(
            reverse("api:paste-id", args=[self.shadowbanned_paste.id])
            + "?api_key="
            + self.shadowbanned_user.api_key
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["pastes"]), 1)
        self.assertEqual(response.json()["pastes"][0]["id"], self.shadowbanned_paste.id)

    def test_other_user_cannot_see_shadowbanned_paste(self):
        """Other users should not be able to see shadowbanned user's paste via API."""
        response = self.client.get(
            reverse("api:paste-id", args=[self.shadowbanned_paste.id])
            + "?api_key="
            + self.other_user.api_key
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["pastes"]), 0)  # Empty result, not found

    def test_normal_user_can_see_normal_paste(self):
        """Normal users should be able to see normal paste via API."""
        response = self.client.get(
            reverse("api:paste-id", args=[self.normal_paste.id])
            + "?api_key="
            + self.other_user.api_key
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["pastes"]), 1)
        self.assertEqual(response.json()["pastes"][0]["id"], self.normal_paste.id)

    def test_shadowbanned_user_can_see_normal_paste(self):
        """Shadowbanned users should still be able to see normal user pastes via API."""
        response = self.client.get(
            reverse("api:paste-id", args=[self.normal_paste.id])
            + "?api_key="
            + self.shadowbanned_user.api_key
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["pastes"]), 1)
        self.assertEqual(response.json()["pastes"][0]["id"], self.normal_paste.id)

    def test_anonymous_user_cannot_see_shadowbanned_paste(self):
        """Anonymous users (no API key) should not be able to see shadowbanned user's paste via API."""
        response = self.client.get(
            reverse("api:paste-id", args=[self.shadowbanned_paste.id])
        )
        self.assertEqual(
            response.status_code, 422
        )  # Schema validation error for missing api_key

    def test_invalid_api_key_cannot_see_shadowbanned_paste(self):
        """Users with invalid API key should not be able to see shadowbanned user's paste via API."""
        response = self.client.get(
            reverse("api:paste-id", args=[self.shadowbanned_paste.id])
            + "?api_key=invalid_key"
        )
        self.assertEqual(
            response.status_code, 422
        )  # Schema validation error for invalid api_key

    def test_shadowbanned_user_can_list_own_pastes(self):
        """Shadowbanned user should be able to list their own pastes via API."""
        response = self.client.get(
            reverse("api:paste") + "?api_key=" + self.shadowbanned_user.api_key
        )
        self.assertEqual(response.status_code, 200)
        pastes = response.json()["pastes"]
        self.assertEqual(len(pastes), 1)
        self.assertEqual(pastes[0]["id"], self.shadowbanned_paste.id)

    def test_normal_user_can_list_own_pastes(self):
        """Normal user should be able to list their own pastes via API."""
        response = self.client.get(
            reverse("api:paste") + "?api_key=" + self.normal_user.api_key
        )
        self.assertEqual(response.status_code, 200)
        pastes = response.json()["pastes"]
        self.assertEqual(len(pastes), 1)
        self.assertEqual(pastes[0]["id"], self.normal_paste.id)

    def test_shadowbanned_user_paste_includes_body_when_requested(self):
        """Shadowbanned user should get full paste body when requesting their own paste via API."""
        response = self.client.get(
            reverse("api:paste-id", args=[self.shadowbanned_paste.id])
            + "?api_key="
            + self.shadowbanned_user.api_key
        )
        self.assertEqual(response.status_code, 200)
        paste_data = response.json()["pastes"][0]
        self.assertEqual(paste_data["id"], self.shadowbanned_paste.id)
        self.assertIn(
            "body", paste_data
        )  # Body should be included for specific paste requests
        self.assertEqual(paste_data["body"], self.shadowbanned_paste.body)

    def test_normal_user_paste_includes_body_when_requested(self):
        """Normal user should get full paste body when requesting specific paste via API."""
        response = self.client.get(
            reverse("api:paste-id", args=[self.normal_paste.id])
            + "?api_key="
            + self.other_user.api_key
        )
        self.assertEqual(response.status_code, 200)
        paste_data = response.json()["pastes"][0]
        self.assertEqual(paste_data["id"], self.normal_paste.id)
        self.assertIn(
            "body", paste_data
        )  # Body should be included for specific paste requests
        self.assertEqual(paste_data["body"], self.normal_paste.body)
