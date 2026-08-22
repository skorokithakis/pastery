import contextlib
from datetime import timedelta

import sentry_sdk
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.transport import Transport

from .models import Paste

User = get_user_model()


class RecordingTransport(Transport):
    """Records every envelope it receives instead of sending it, keeping
    the smoke test off the network."""

    def __init__(self):
        super().__init__()
        self.envelopes = []

    def capture_envelope(self, envelope):
        self.envelopes.append(envelope)


@contextlib.contextmanager
def sentry_with_recording_transport():
    """Temporarily initialise Sentry with a fake DSN and the recording
    transport, restoring whatever client was active before."""
    previous_client = sentry_sdk.get_client()
    transport = RecordingTransport()
    try:
        # A fake DSN with a no-op transport: DjangoIntegration.setup_once()
        # runs at init time and must not fail on Django 2.0, but no event
        # can ever reach the network.
        sentry_sdk.init(dsn="https://public@fake.example.com/1", transport=transport)
        yield transport
    finally:
        sentry_sdk.get_client().close()
        sentry_sdk.get_global_scope().set_client(previous_client)


class SentrySmokeTests(TestCase):
    def test_django_integration_binds_without_network(self):
        # With no SENTRY_DSN set, settings.py must not initialize Sentry at
        # all, so nothing else in the suite exercises the Django integration.
        self.assertFalse(sentry_sdk.is_initialized())

        with sentry_with_recording_transport() as transport:
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
            # The capture must actually reach the transport: without this
            # assertion the test would pass even if capturing were broken.
            self.assertEqual(len(transport.envelopes), 1)

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

    def test_sitemap_xml(self):
        # The only pattern in main/urls.py registered with an unanchored
        # plain string; pin it so a Django upgrade can't silently break it.
        response = self.client.get("/sitemap.xml")
        self.assertEqual(response.status_code, 200)

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

    def test_paste_views_are_noindexed(self):
        # Every view that serves paste content must tell crawlers to leave
        # it out of their indexes; a meta tag is impossible on the two
        # text/plain views, which is why this is a header.
        for url_name in (
            "main:paste",
            "main:raw-paste",
            "main:download-paste",
            "main:embed-paste",
        ):
            response = self.client.get(reverse(url_name, args=[self.paste1.id]))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response["X-Robots-Tag"], "noindex, nofollow")

    def test_clone_home_is_noindexed_but_home_is_not(self):
        # ?clone=<id> loads a paste's body into the home form, so that
        # response must carry the crawler directive; the plain home page
        # must stay indexable.
        response = self.client.get(reverse("main:home"))
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("X-Robots-Tag", response)

        response = self.client.get(reverse("main:home") + "?clone=" + self.paste1.id)
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

    def test_report_paste_reports_to_sentry(self):
        # The successful report path is the one place in the codebase that
        # reports to Sentry, so it must run and actually reach a transport.
        # report_paste is limited at 2/m on the shared default cache and
        # other tests in this class have already reported from the test
        # client's IP, so clear the counters first to keep this POST
        # un-limited (and leave no leftovers for later tests).
        cache.clear()
        self.client.force_login(self.user1, backend=settings.AUTHENTICATION_BACKENDS[0])
        url = reverse("main:report-paste", args=[self.paste1.id])

        with sentry_with_recording_transport() as transport:
            response = self.client.post(url, follow=True)
            self.assertRedirects(response, reverse("main:home"))
            self.assertEqual(
                str(list(response.context["messages"])[0]),
                "Thank you for your report. We will investigate as soon as possible.",
            )
            sentry_sdk.flush(timeout=1)
            self.assertEqual(len(transport.envelopes), 1)

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


class WebauthinSmokeTests(TestCase):
    """django-webauthin 0.0.8 replaced the whole challenge flow
    (py_webauthn 0.4 -> 2.x) and nothing else in the suite touches its
    endpoints, so pin down the two halves of the login flow that work
    without a real credential: the rendered login page and the
    login-begin challenge hand-off. The verify endpoints need a signing
    authenticator and stay out of scope."""

    def test_login_page_renders_webauthin_login_markup(self):
        # main/templates/login.html includes webauthin_login.html, whose
        # script fetches the login-begin endpoint and binds the
        # #webauthin-login button.
        response = self.client.get(reverse("main:login"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="webauthin-login"')
        self.assertContains(response, reverse("webauthin:login-begin"))

    def test_login_begin_returns_challenge_and_stores_it_in_session(self):
        response = self.client.post(reverse("webauthin:login-begin"))
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("challenge", payload)
        # login_verify pops the challenge out of the session, so it must
        # have been stored by login_begin.
        self.assertEqual(self.client.session["challenge"], payload["challenge"])
