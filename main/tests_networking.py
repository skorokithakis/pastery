# Cross-cutting tests: the client IP that the rate limiter and the spam
# blocker key on, and the rate limiting itself.

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache
from django.test import RequestFactory
from django.test import TestCase
from django.urls import reverse

from pastery.ratelimit import get_client_ip
from pastery.ratelimit import rate_limit_key

from .models import Paste

User = get_user_model()


class ClientIPTests(TestCase):
    """The client IP is resolved from the Cloudflare trust chain.

    CF-Connecting-IP is only trusted when the peer (the right-most
    X-Forwarded-For entry, or REMOTE_ADDR when the header is absent) is a
    real Cloudflare address from the ranges committed in pastery/ratelimit.py.
    """

    def test_cf_connecting_ip_is_honoured_when_the_peer_is_cloudflare(self):
        # 173.245.48.1 is inside the committed 173.245.48.0/20 range.
        request = RequestFactory().get("/")
        request.META["REMOTE_ADDR"] = "10.0.0.5"
        request.META["HTTP_X_FORWARDED_FOR"] = "173.245.48.1"
        request.META["HTTP_CF_CONNECTING_IP"] = "5.6.7.8"
        self.assertEqual(get_client_ip(request), "5.6.7.8")

    def test_forged_cf_connecting_ip_is_ignored_when_the_peer_is_not_cloudflare(self):
        # A direct-to-origin attacker cannot make the resolver trust their
        # header: the peer is the trust anchor, and 9.9.9.9 is not a
        # Cloudflare address, so the forged header is ignored entirely.
        request = RequestFactory().get("/")
        request.META["REMOTE_ADDR"] = "10.0.0.5"
        request.META["HTTP_X_FORWARDED_FOR"] = "9.9.9.9"
        request.META["HTTP_CF_CONNECTING_IP"] = "5.6.7.8"
        self.assertEqual(get_client_ip(request), "9.9.9.9")

    def test_remote_addr_is_the_fallback_when_xff_is_absent(self):
        # The runserver and test-client case: no X-Forwarded-For at all.
        request = RequestFactory().get("/")
        request.META["REMOTE_ADDR"] = "1.2.3.4"
        self.assertEqual(get_client_ip(request), "1.2.3.4")

    def test_cloudflare_peer_without_connecting_ip_falls_back_to_the_peer(self):
        # 2606:4700::1 is inside the committed 2606:4700::/32 range.
        request = RequestFactory().get("/")
        request.META["HTTP_X_FORWARDED_FOR"] = "2606:4700::1"
        self.assertEqual(get_client_ip(request), "2606:4700::1")

    def test_ipv4_mapped_ipv6_peer_is_normalised_before_the_range_check(self):
        # ::ffff:173.245.48.1 is the IPv4-mapped form of a Cloudflare
        # address; it must match the ranges as plain IPv4, not as an IPv6
        # address that is in no range.
        request = RequestFactory().get("/")
        request.META["HTTP_X_FORWARDED_FOR"] = "::ffff:173.245.48.1"
        request.META["HTTP_CF_CONNECTING_IP"] = "5.6.7.8"
        self.assertEqual(get_client_ip(request), "5.6.7.8")

    def test_malformed_headers_do_not_raise(self):
        request = RequestFactory().get("/")
        request.META["REMOTE_ADDR"] = ""
        request.META["HTTP_X_FORWARDED_FOR"] = "not-an-ip, also-junk"
        request.META["HTTP_CF_CONNECTING_IP"] = "junk"
        self.assertEqual(get_client_ip(request), "")


class RateLimitKeyTests(TestCase):
    """rate_limit_key buckets IPv4 clients by address and IPv6 by /64."""

    def _key_for_client(self, client_ip):
        # The peer is a real Cloudflare address (104.16.0.0/13), so the
        # CF-Connecting-IP header is trusted.
        request = RequestFactory().get("/")
        request.META["HTTP_X_FORWARDED_FOR"] = "104.16.0.1"
        request.META["HTTP_CF_CONNECTING_IP"] = client_ip
        return rate_limit_key("test", request)

    def test_ipv4_clients_are_bucketed_by_their_full_address(self):
        self.assertEqual(self._key_for_client("203.0.113.7"), "203.0.113.7")

    def test_ipv6_clients_in_one_64_share_a_bucket(self):
        self.assertEqual(
            self._key_for_client("2001:db8:1:2::1"),
            self._key_for_client("2001:db8:1:2::ffff"),
        )
        self.assertEqual(self._key_for_client("2001:db8:1:2::1"), "2001:db8:1:2::/64")

    def test_ipv6_clients_in_different_64s_do_not_share_a_bucket(self):
        self.assertNotEqual(
            self._key_for_client("2001:db8:1:2::1"),
            self._key_for_client("2001:db8:1:3::1"),
        )

    def test_ipv4_mapped_ipv6_client_gets_a_plain_ipv4_bucket(self):
        # ::ffff:203.0.113.7 must not be collapsed into a nonsense /64.
        self.assertEqual(self._key_for_client("::ffff:203.0.113.7"), "203.0.113.7")


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
        # The key is rate_limit_key, which trusts CF-Connecting-IP only
        # when the peer is a Cloudflare address. The X-Forwarded-For here
        # carries 173.245.48.1, inside the committed 173.245.48.0/20 range,
        # so the header is honoured. Every request shares the test client's
        # default REMOTE_ADDR, so if the key fell back to REMOTE_ADDR (or
        # to django-ratelimit's built-in 'ip' key) the request from 2.2.2.2
        # would also be limited. As in test_limited_view_returns_429, the
        # counter starts at 1 and trips when it is exceeded, so the 21st
        # request is the first one over 20/m.
        url = reverse("main:paste", args=[self.paste.id])
        xff = {"HTTP_X_FORWARDED_FOR": "173.245.48.1"}
        for _ in range(20):
            response = self.client.get(url, HTTP_CF_CONNECTING_IP="1.1.1.1", **xff)
            self.assertEqual(response.status_code, 200)

        response = self.client.get(url, HTTP_CF_CONNECTING_IP="1.1.1.1", **xff)
        self.assertEqual(response.status_code, 429)

        response = self.client.get(url, HTTP_CF_CONNECTING_IP="2.2.2.2", **xff)
        self.assertEqual(response.status_code, 200)

    def test_forged_cf_connecting_ip_cannot_choose_its_own_bucket(self):
        # A request that did not come through Cloudflare must not be able
        # to pick its rate limit bucket: the test client sends no
        # X-Forwarded-For, so the peer is its REMOTE_ADDR, and the
        # CF-Connecting-IP header is ignored. Rotating the header therefore
        # changes nothing, and the 21st request trips the 20/m limit even
        # with a fresh forged value. This is the rep-woxjr criterion.
        url = reverse("main:paste", args=[self.paste.id])
        for i in range(20):
            response = self.client.get(url, HTTP_CF_CONNECTING_IP="1.1.1.%d" % i)
            self.assertEqual(response.status_code, 200)

        response = self.client.get(url, HTTP_CF_CONNECTING_IP="2.2.2.2")
        self.assertEqual(response.status_code, 429)

    def test_ipv6_clients_in_one_64_share_a_rate_limit_bucket(self):
        # The peer is a real Cloudflare IPv6 address (2606:4700::/32), so
        # CF-Connecting-IP is trusted, and rate_limit_key collapses the
        # client to its /64: rotating addresses within the /64 cannot
        # defeat the 20/m limit, while a different /64 gets a fresh bucket.
        url = reverse("main:paste", args=[self.paste.id])
        xff = {"HTTP_X_FORWARDED_FOR": "2606:4700::1"}
        for _ in range(20):
            response = self.client.get(
                url, HTTP_CF_CONNECTING_IP="2001:db8:1:2::1", **xff
            )
            self.assertEqual(response.status_code, 200)

        response = self.client.get(url, HTTP_CF_CONNECTING_IP="2001:db8:1:2::2", **xff)
        self.assertEqual(response.status_code, 429)

        response = self.client.get(url, HTTP_CF_CONNECTING_IP="2001:db8:1:3::1", **xff)
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
