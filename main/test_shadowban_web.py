from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import Http404
from django.test import TestCase
from django.urls import reverse

from .models import Paste

User = get_user_model()


class ShadowbanWebViewTests(TestCase):
    def setUp(self):
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

    def test_shadowbanned_user_can_view_own_paste(self):
        """Shadowbanned user should be able to view their own paste via web."""
        self.client.force_login(
            self.shadowbanned_user, backend=settings.AUTHENTICATION_BACKENDS[0]
        )
        response = self.client.get(
            reverse("main:paste", args=[self.shadowbanned_paste.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["paste"].id, self.shadowbanned_paste.id)

    def test_other_user_cannot_view_shadowbanned_paste(self):
        """Other users should not be able to view shadowbanned user's paste via web."""
        self.client.force_login(
            self.other_user, backend=settings.AUTHENTICATION_BACKENDS[0]
        )
        response = self.client.get(
            reverse("main:paste", args=[self.shadowbanned_paste.id])
        )
        self.assertEqual(response.status_code, 404)

    def test_anonymous_user_cannot_view_shadowbanned_paste(self):
        """Anonymous users should not be able to view shadowbanned user's paste via web."""
        response = self.client.get(
            reverse("main:paste", args=[self.shadowbanned_paste.id])
        )
        self.assertEqual(response.status_code, 404)

    def test_normal_user_can_view_normal_paste(self):
        """Normal users should be able to view normal pastes via web."""
        self.client.force_login(
            self.other_user, backend=settings.AUTHENTICATION_BACKENDS[0]
        )
        response = self.client.get(reverse("main:paste", args=[self.normal_paste.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["paste"].id, self.normal_paste.id)

    def test_shadowbanned_user_can_view_normal_paste(self):
        """Shadowbanned users should still be able to view normal user pastes via web."""
        self.client.force_login(
            self.shadowbanned_user, backend=settings.AUTHENTICATION_BACKENDS[0]
        )
        response = self.client.get(reverse("main:paste", args=[self.normal_paste.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["paste"].id, self.normal_paste.id)

    def test_shadowbanned_user_can_download_own_paste(self):
        """Shadowbanned user should be able to download their own paste."""
        self.client.force_login(
            self.shadowbanned_user, backend=settings.AUTHENTICATION_BACKENDS[0]
        )
        response = self.client.get(
            reverse("main:download-paste", args=[self.shadowbanned_paste.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), self.shadowbanned_paste.body)

    def test_other_user_cannot_download_shadowbanned_paste(self):
        """Other users should not be able to download shadowbanned user's paste."""
        self.client.force_login(
            self.other_user, backend=settings.AUTHENTICATION_BACKENDS[0]
        )
        response = self.client.get(
            reverse("main:download-paste", args=[self.shadowbanned_paste.id])
        )
        self.assertEqual(response.status_code, 404)

    def test_shadowbanned_user_can_view_raw_own_paste(self):
        """Shadowbanned user should be able to view raw version of their own paste."""
        self.client.force_login(
            self.shadowbanned_user, backend=settings.AUTHENTICATION_BACKENDS[0]
        )
        response = self.client.get(
            reverse("main:raw-paste", args=[self.shadowbanned_paste.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), self.shadowbanned_paste.body)

    def test_other_user_cannot_view_raw_shadowbanned_paste(self):
        """Other users should not be able to view raw version of shadowbanned user's paste."""
        self.client.force_login(
            self.other_user, backend=settings.AUTHENTICATION_BACKENDS[0]
        )
        response = self.client.get(
            reverse("main:raw-paste", args=[self.shadowbanned_paste.id])
        )
        self.assertEqual(response.status_code, 404)

    def test_shadowbanned_user_can_embed_own_paste(self):
        """Shadowbanned user should be able to embed their own paste."""
        self.client.force_login(
            self.shadowbanned_user, backend=settings.AUTHENTICATION_BACKENDS[0]
        )
        response = self.client.get(
            reverse("main:embed-paste", args=[self.shadowbanned_paste.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.shadowbanned_paste, response.context["pastes"])

    def test_other_user_cannot_embed_shadowbanned_paste(self):
        """Other users should not be able to embed shadowbanned user's paste."""
        self.client.force_login(
            self.other_user, backend=settings.AUTHENTICATION_BACKENDS[0]
        )
        response = self.client.get(
            reverse("main:embed-paste", args=[self.shadowbanned_paste.id])
        )
        self.assertEqual(response.status_code, 404)

    def test_anonymous_user_cannot_embed_shadowbanned_paste(self):
        """Anonymous users should not be able to embed shadowbanned user's paste."""
        response = self.client.get(
            reverse("main:embed-paste", args=[self.shadowbanned_paste.id])
        )
        self.assertEqual(response.status_code, 404)

    def test_shadowbanned_user_can_oembed_own_paste(self):
        """Shadowbanned user should be able to oembed their own paste."""
        self.client.force_login(
            self.shadowbanned_user, backend=settings.AUTHENTICATION_BACKENDS[0]
        )
        response = self.client.post(
            reverse("main:oembed")
            + f"?url=https://example.com/{self.shadowbanned_paste.id}"
        )
        self.assertEqual(response.status_code, 200)

    def test_other_user_cannot_oembed_shadowbanned_paste(self):
        """Other users should not be able to oembed shadowbanned user's paste."""
        self.client.force_login(
            self.other_user, backend=settings.AUTHENTICATION_BACKENDS[0]
        )
        response = self.client.post(
            reverse("main:oembed")
            + f"?url=https://example.com/{self.shadowbanned_paste.id}"
        )
        self.assertEqual(response.status_code, 404)

    def test_multiple_paste_embed_with_shadowbanned_paste(self):
        """Test multiple paste embed where one paste is shadowbanned."""
        # Other user should only see normal paste, not shadowbanned paste
        self.client.force_login(
            self.other_user, backend=settings.AUTHENTICATION_BACKENDS[0]
        )
        paste_combo = f"{self.normal_paste.id}+{self.shadowbanned_paste.id}"
        response = self.client.get(reverse("main:embed-paste", args=[paste_combo]))
        self.assertEqual(response.status_code, 200)
        pastes = response.context["pastes"]
        self.assertEqual(len(pastes), 2)
        self.assertEqual(pastes[0], self.normal_paste)
        self.assertIsNone(pastes[1])  # Shadowbanned paste should be None

    def test_multiple_paste_view_with_shadowbanned_paste_as_owner(self):
        """Test multiple paste view where shadowbanned user can see their own paste."""
        self.client.force_login(
            self.shadowbanned_user, backend=settings.AUTHENTICATION_BACKENDS[0]
        )
        paste_combo = f"{self.normal_paste.id}+{self.shadowbanned_paste.id}"
        response = self.client.get(reverse("main:paste", args=[paste_combo]))
        self.assertEqual(response.status_code, 200)
        pastes = response.context["pastes"]
        self.assertEqual(len(pastes), 2)
        self.assertEqual(pastes[0], self.normal_paste)
        self.assertEqual(pastes[1], self.shadowbanned_paste)


class ShadowbanModelTests(TestCase):
    def setUp(self):
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

    def test_get_by_id_or_404_shadowbanned_user_can_access_own_paste(self):
        """Shadowbanned user should be able to access their own paste via get_by_id_or_404."""
        paste = Paste.get_by_id_or_404(
            self.shadowbanned_paste.id, self.shadowbanned_user
        )
        self.assertEqual(paste, self.shadowbanned_paste)

    def test_get_by_id_or_404_other_user_cannot_access_shadowbanned_paste(self):
        """Other users should not be able to access shadowbanned user's paste via get_by_id_or_404."""
        with self.assertRaises(Http404):
            Paste.get_by_id_or_404(self.shadowbanned_paste.id, self.other_user)

    def test_get_by_id_or_404_anonymous_user_cannot_access_shadowbanned_paste(self):
        """Anonymous users should not be able to access shadowbanned user's paste via get_by_id_or_404."""
        with self.assertRaises(Http404):
            Paste.get_by_id_or_404(self.shadowbanned_paste.id, None)

    def test_get_by_id_or_404_unauthenticated_user_cannot_access_shadowbanned_paste(
        self,
    ):
        """Unauthenticated users should not be able to access shadowbanned user's paste via get_by_id_or_404."""

        # Create mock unauthenticated user
        class MockUser:
            is_authenticated = False

        mock_user = MockUser()
        with self.assertRaises(Http404):
            Paste.get_by_id_or_404(self.shadowbanned_paste.id, mock_user)

    def test_get_by_id_or_404_normal_paste_accessible_by_all(self):
        """Normal pastes should be accessible by all users via get_by_id_or_404."""
        # Test with normal user
        paste = Paste.get_by_id_or_404(self.normal_paste.id, self.normal_user)
        self.assertEqual(paste, self.normal_paste)

        # Test with shadowbanned user
        paste = Paste.get_by_id_or_404(self.normal_paste.id, self.shadowbanned_user)
        self.assertEqual(paste, self.normal_paste)

        # Test with other user
        paste = Paste.get_by_id_or_404(self.normal_paste.id, self.other_user)
        self.assertEqual(paste, self.normal_paste)

        # Test with anonymous user
        paste = Paste.get_by_id_or_404(self.normal_paste.id, None)
        self.assertEqual(paste, self.normal_paste)
