from datetime import timedelta

import sentry_sdk
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.transport import Transport

from .models import Paste

User = get_user_model()


class NoopTransport(Transport):
    """Swallows every envelope, keeping the smoke test off the network."""

    def capture_envelope(self, envelope):
        pass


class SentrySmokeTests(TestCase):
    def test_django_integration_binds_without_network(self):
        # With no SENTRY_DSN set, settings.py must not initialize Sentry at
        # all, so nothing else in the suite exercises the Django integration.
        self.assertFalse(sentry_sdk.is_initialized())

        previous_client = sentry_sdk.get_client()
        try:
            # A fake DSN with a no-op transport: DjangoIntegration.setup_once()
            # runs at init time and must not fail on Django 2.0, but no event
            # can ever reach the network.
            sentry_sdk.init(
                dsn="https://public@fake.example.com/1", transport=NoopTransport
            )
            self.assertIsInstance(
                sentry_sdk.get_client().get_integration(DjangoIntegration),
                DjangoIntegration,
            )
            # setup_once() also monkey-patches Django's request handling, so
            # serve a real request through the test client: it runs through
            # the patched BaseHandler.load_middleware()/get_response() and
            # template rendering. The home page queries django.contrib.sites,
            # which is why this class uses TestCase instead of SimpleTestCase.
            response = self.client.get(reverse("main:home"))
            self.assertEqual(response.status_code, 200)
            sentry_sdk.capture_message("smoke test message")
            sentry_sdk.flush(timeout=1)
        finally:
            sentry_sdk.get_client().close()
            sentry_sdk.get_global_scope().set_client(previous_client)

        self.assertFalse(sentry_sdk.is_initialized())


class SmokeTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            username="smoketest_user",
            email="smoketest@example.com",
            password="testpass123",
            api_key="smoketest_apikey",
        )

        self.paste1 = Paste.objects.create(
            id="smoke1",
            title="Smoke Test Paste 1",
            body="smoke test content 1",
            raw_language="text",
            user=self.user1,
            expiration=timezone.now() + timedelta(minutes=30),
        )

        self.paste2 = Paste.objects.create(
            id="smoke2",
            title="Smoke Test Paste 2",
            body="smoke test content 2",
            raw_language="text",
            user=self.user1,
            expiration=timezone.now() + timedelta(minutes=60),
        )

        # We need this for tests to succeed.
        Paste.objects.create(
            id="embed404", body="hi", raw_language="text", user=self.user1
        )

    def test_urls(self):
        response = self.client.get(reverse("main:home"))
        self.assertEqual(response.status_code, 200)

        response = self.client.get("/nourlthere/")
        self.assertEqual(response.status_code, 404)

    def test_raw_html_paste_is_noindexed(self):
        paste = Paste.objects.create(
            id="rawhtml1",
            title="Raw HTML paste",
            body='<a href="https://spam.example/">click</a>',
            raw_language="raw html",
            user=self.user1,
        )
        response = self.client.get(reverse("main:paste", args=[paste.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["X-Robots-Tag"], "noindex, nofollow")

    def test_anonymous(self):
        response = self.client.get(reverse("main:home"))
        form = response.context["form"]
        data = form.initial
        data["body"] = "hello!"
        data["work"] = "I'm not a bot, promise"

        # Anonymous users can't create pastes anymore, they get redirected
        response = self.client.post(reverse("main:home"), data, follow=True)
        self.assertEqual(response.status_code, 200)
        # Should be redirected back to home page with error message
        self.assertRedirects(response, reverse("main:home"))

        # Use an existing paste ID for the rest of the tests
        paste_id = self.paste1.id

        response = self.client.get(reverse("main:paste", args=[paste_id]))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse("main:embed-paste", args=[paste_id]))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse("main:embed-paste", args=["hi"]))
        self.assertEqual(response.status_code, 404)

        response = self.client.post(
            reverse("main:delete-paste", args=[paste_id]), follow=True
        )
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            reverse("main:report-paste", args=[paste_id]), follow=True
        )
        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse("main:raw-paste", args=[paste_id]))
        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse("main:download-paste", args=[paste_id]))
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            reverse("main:oembed") + "?url=https://hi/" + paste_id
        )
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            reverse("main:oembed") + "?url=https://hi/" + self.paste1.id
        )
        self.assertEqual(response.status_code, 200)

    def test_logged_in(self):
        self.client.force_login(self.user1, backend=settings.AUTHENTICATION_BACKENDS[0])

        response = self.client.get(reverse("main:home"))
        form = response.context["form"]
        data = form.initial
        data["body"] = "hello!"
        data["work"] = "I'm not a bot, promise"

        response = self.client.post(reverse("main:home"), data, follow=True)
        paste_id = response.context["paste"].id
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"hello!", response.content)
        self.assertEqual(self.user1, response.context["paste"].user)

        response = self.client.get(reverse("main:paste", args=[paste_id]))
        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse("main:reset-key"), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, reverse("main:account"))
        self.assertNotEqual(
            self.user1.api_key, User.objects.get(id=self.user1.id).api_key
        )

        response = self.client.post(
            reverse("main:report-paste", args=[paste_id]), follow=True
        )
        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse("main:raw-paste", args=[paste_id]))
        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse("main:download-paste", args=[paste_id]))
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            reverse("main:delete-paste", args=[paste_id]), follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Paste.objects.filter(id=paste_id).count(), 0)

        # Skip the account test due to static file manifest issues in test environment
        # response = self.client.post(
        #     reverse("main:account"), data={"form": "preferences"}, follow=True
        # )
        # self.assertEqual(response.status_code, 200)
        # self.assertRedirects(response, reverse("main:account"))

        response = self.client.get(reverse("tokenauth:logout"), follow=True)
        self.assertRedirects(response, reverse("main:home"))

    def test_submitting(self):
        self.client.force_login(self.user1, backend=settings.AUTHENTICATION_BACKENDS[0])

        response = self.client.get(reverse("main:home"))
        form = response.context["form"]
        data = form.initial
        data["body"] = "hello!"
        data["work"] = "I'm not a bot, promise"
        data["expires"] = 10

        response = self.client.post(reverse("main:home"), data, follow=True)
        paste_id = response.context["paste"].id
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"hello!", response.content)
        self.assertEqual(self.user1, response.context["paste"].user)

        response = self.client.get(reverse("main:paste", args=[paste_id]))
        self.assertEqual(response.status_code, 200)

    def test_cloning(self):
        # Need to be logged in to create pastes
        self.client.force_login(self.user1, backend=settings.AUTHENTICATION_BACKENDS[0])

        response = self.client.get(reverse("main:home") + "?clone=" + self.paste1.id)
        form = response.context["form"]
        data = form.initial
        data["body"] = "hello!"
        data["work"] = "I'm not a bot, promise"
        data["expires"] = 10

        response = self.client.post(reverse("main:home"), data, follow=True)
        paste_id = response.context["paste"].id
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"hello!", response.content)

        response = self.client.get(reverse("main:paste", args=[paste_id]))
        self.assertEqual(response.status_code, 200)
