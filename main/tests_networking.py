# Cross-cutting tests: the client IP that the rate limiter and the spam
# blocker key on, and the rate limiting itself.

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import RequestFactory
from django.test import TestCase
from django.urls import reverse
from ipware import get_client_ip

from .models import Paste

User = get_user_model()


class ClientIPTests(TestCase):
    """The configured IPWARE_META_PRECEDENCE_ORDER is honoured."""

    def test_cf_connecting_ip_wins_over_remote_addr(self):
        request = RequestFactory().get("/")
        request.META["REMOTE_ADDR"] = "1.2.3.4"
        request.META["HTTP_X_FORWARDED_FOR"] = "9.9.9.9"
        request.META["HTTP_CF_CONNECTING_IP"] = "5.6.7.8"
        ip, _ = get_client_ip(request)
        self.assertEqual(ip, "5.6.7.8")

    def test_remote_addr_is_the_fallback(self):
        request = RequestFactory().get("/")
        request.META["REMOTE_ADDR"] = "1.2.3.4"
        ip, _ = get_client_ip(request)
        self.assertEqual(ip, "1.2.3.4")


class RateLimitTests(TestCase):
    """Both block=True and block=False views honour the rate limit.

    The cache is cleared in setUp/tearDown so the counters never leak into
    other test classes (and vice versa): the rate limiting counts by IP on
    the shared default cache.
    """

    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(
            username="ratelimit_user",
            email="ratelimit@example.com",
            password="testpass123",
        )
        self.paste = Paste.objects.create(
            id="rl123",
            body="rate limited paste",
            raw_language="text",
            user=self.user,
        )

    def tearDown(self):
        cache.clear()

    def test_block_true_view_returns_429(self):
        # The paste view is limited at 20/m with block=True. brake's cache
        # backend seeds a fresh counter with 1 and then increments it, so the
        # first request leaves the counter at 2: the 21st request is the
        # first one over the limit.
        url = reverse("main:paste", args=[self.paste.id])
        for _ in range(20):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 429)

    def test_block_false_view_marks_request_limited(self):
        # report_paste is limited at 2/m with block=False: the limited
        # request still runs, but the view sees request.limited and
        # redirects to the paste instead of reporting it. As in
        # test_block_true_view_returns_429, brake's seeded counter makes the
        # limit trip one request earlier than the rate suggests: the third
        # POST is the one over 2/m.
        self.client.force_login(self.user, backend=settings.AUTHENTICATION_BACKENDS[0])
        url = reverse("main:report-paste", args=[self.paste.id])
        for _ in range(2):
            response = self.client.post(url)
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response["Location"], "/")

        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/rl123/")
