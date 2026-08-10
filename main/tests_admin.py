# Admin tests: changelists are exercised so regressions in the admin are
# caught. Note that .coveragerc omits admin.py, so these tests never
# contribute to the coverage report.

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Paste

User = get_user_model()


class AdminChangelistTests(TestCase):
    """Every registered changelist loads as a superuser."""

    def setUp(self):
        self.superuser = User.objects.create_superuser(
            username="admin_user",
            email="admin@example.com",
            password="testpass123",
        )
        self.client.force_login(
            self.superuser, backend=settings.AUTHENTICATION_BACKENDS[0]
        )

    def test_all_registered_changelists_return_200(self):
        for changelist_name in [
            "admin:main_paste_changelist",
            "admin:main_user_changelist",
            "admin:main_setting_changelist",
        ]:
            with self.subTest(changelist=changelist_name):
                response = self.client.get(reverse(changelist_name))
                self.assertEqual(response.status_code, 200)


class ShadowbannedUserFilterTests(TestCase):
    """Both values of the ShadowbannedUserFilter are exercised."""

    def setUp(self):
        self.superuser = User.objects.create_superuser(
            username="filter_admin",
            email="filteradmin@example.com",
            password="testpass123",
        )
        self.normal_user = User.objects.create_user(
            username="filter_normal",
            email="filternormal@example.com",
            password="testpass123",
        )
        self.shadowbanned_user = User.objects.create_user(
            username="filter_shadow",
            email="filtershadow@example.com",
            password="testpass123",
            shadowbanned=True,
        )
        self.normal_paste = Paste.objects.create(
            id="fltnrm",
            body="A normal paste",
            raw_language="text",
            user=self.normal_user,
        )
        self.shadowbanned_paste = Paste.objects.create(
            id="fltsb",
            body="A shadowbanned paste",
            raw_language="text",
            user=self.shadowbanned_user,
        )
        self.client.force_login(
            self.superuser, backend=settings.AUTHENTICATION_BACKENDS[0]
        )

    def test_filter_yes_shows_only_shadowbanned_pastes(self):
        response = self.client.get(
            reverse("admin:main_paste_changelist") + "?user_shadowbanned=yes"
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "fltsb")
        self.assertNotContains(response, "fltnrm")

    def test_filter_no_shows_only_non_shadowbanned_pastes(self):
        response = self.client.get(
            reverse("admin:main_paste_changelist") + "?user_shadowbanned=no"
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "fltnrm")
        self.assertNotContains(response, "fltsb")
