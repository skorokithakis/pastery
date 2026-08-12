# Cross-cutting tests: the client IP that the rate limiter and the spam
# blocker key on, and the rate limiting itself.

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import mail
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
    """The rate limited views honour their limits.

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

    def test_limited_view_returns_429(self):
        # The paste view is limited at 20/m. The counter starts at 1 on the
        # first request and the limit trips when it is exceeded, so the
        # 21st request is the first one over the limit.
        url = reverse("main:paste", args=[self.paste.id])
        for _ in range(20):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 429)

    def test_cf_connecting_ip_gets_its_own_bucket(self):
        # The key is rate_limit_key, which resolves the client IP through
        # Cloudflare's HTTP_CF_CONNECTING_IP header. Every request here
        # shares the test client's default REMOTE_ADDR, so if the key fell
        # back to REMOTE_ADDR (or to django-ratelimit's built-in 'ip' key)
        # the request from 2.2.2.2 would also be limited. As in
        # test_limited_view_returns_429, the counter starts at 1 and trips
        # when it is exceeded, so the 21st request is the first one over
        # 20/m.
        url = reverse("main:paste", args=[self.paste.id])
        for _ in range(20):
            response = self.client.get(url, HTTP_CF_CONNECTING_IP="1.1.1.1")
            self.assertEqual(response.status_code, 200)

        response = self.client.get(url, HTTP_CF_CONNECTING_IP="1.1.1.1")
        self.assertEqual(response.status_code, 429)

        response = self.client.get(url, HTTP_CF_CONNECTING_IP="2.2.2.2")
        self.assertEqual(response.status_code, 200)

    def test_tokenauth_login_keeps_its_rate_limit(self):
        # tokenauth 0.5.1 probes for `ratelimit.decorators` (django-ratelimit
        # 3.x) and then `brake.decorators`, and falls back to a no-op
        # decorator when both fail, so pastery.urls applies the 3/h limit
        # itself. A different email on each POST is the attack that would
        # otherwise go unlimited: the 4th POST is the first one over 3/h
        # and must not send a fourth login email. It is not blocked:
        # email_post sees request.limited itself and redirects to the login
        # URL with a warning instead.
        url = reverse("tokenauth:login")
        for i in range(3):
            response = self.client.post(url, {"email": "login%d@example.com" % i})
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response["Location"], settings.LOGIN_URL)

        response = self.client.post(url, {"email": "login3@example.com"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], settings.LOGIN_URL)
        self.assertEqual(len(mail.outbox), 3)

    def test_tokenauth_login_get_requests_do_not_consume_quota(self):
        # The pastery.urls shim wraps the already-decorated email_post, so
        # it runs before tokenauth's own require_http_methods: GETs are
        # rejected with 405 and must not count towards the 3/h limit. If
        # they did, the first POST below would be the 4th request in the
        # window and would not send a login email.
        url = reverse("tokenauth:login")
        for _ in range(3):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 405)

        for i in range(3):
            response = self.client.post(url, {"email": "getlogin%d@example.com" % i})
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response["Location"], settings.LOGIN_URL)

        self.assertEqual(len(mail.outbox), 3)

    def test_limited_view_redirects_to_paste(self):
        # report_paste is limited at 2/m with block=False: the limited
        # request still runs, but the shared helper sees request.limited
        # and returns the redirect to the paste instead of reporting it.
        # As in test_limited_view_returns_429, the counter starts at 1 and
        # trips when it is exceeded, so the third POST is the first one
        # over 2/m.
        self.client.force_login(self.user, backend=settings.AUTHENTICATION_BACKENDS[0])
        url = reverse("main:report-paste", args=[self.paste.id])
        for _ in range(2):
            response = self.client.post(url)
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response["Location"], "/")

        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/rl123/")

    def test_stacked_decorators_each_count_the_request_once(self):
        # PasteView is limited at 20/m, 500/h and 1000/d on POST. The rate
        # is part of django-ratelimit's cache key, so this test cannot tell
        # the decorators' groups apart. What it does prove is that each
        # stacked decorator counts a request exactly once: after 20 POSTs
        # the 20/m counter is at 20, so the 21st request is the first one
        # over the limit. If every POST were counted three times in one
        # bucket, the limit would trip on the 7th request instead.
        url = reverse("api:paste") + "?api_key=" + self.user.api_key
        for _ in range(20):
            response = self.client.post(
                url, "stuff", content_type="application/x-www-form-urlencoded"
            )
            self.assertEqual(response.status_code, 200)

        response = self.client.post(
            url, "stuff", content_type="application/x-www-form-urlencoded"
        )
        self.assertEqual(response.status_code, 429)
