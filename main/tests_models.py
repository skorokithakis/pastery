# Model tests for main.models, added to pin down rendering behaviour before
# the markdown/textile/bleach/pygments upgrade.

from datetime import timedelta
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone

from .models import Paste

User = get_user_model()


class PasteRenderingTests(TestCase):
    """Tests for Paste.rendered_body, including golden outputs."""

    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(
            username="rendering_user",
            email="rendering@example.com",
            password="testpass123",
        )

    def test_rendered_body_markdown(self):
        paste = Paste.objects.create(
            id="rendermd",
            body="# Hello\n\nSome **bold** text.",
            raw_language="markdown",
            user=self.user,
        )
        rendered = paste.rendered_body
        self.assertIn("<h1>Hello</h1>", rendered)
        self.assertIn("<strong>bold</strong>", rendered)

    def test_rendered_body_textile(self):
        paste = Paste.objects.create(
            id="rendertex",
            body="Some *bold* text.",
            raw_language="textile",
            user=self.user,
        )
        rendered = paste.rendered_body
        self.assertIn("<strong>bold</strong>", rendered)

    def test_golden_pygments_output(self):
        """Byte-exact Pygments rendering.

        This expected string is a deliberate baseline for the vendored
        PasteryFormatter (a copy of old Pygments HtmlFormatter internals).
        A Pygments upgrade is expected to change it; when it does, the diff
        must be reviewed by a human rather than blindly re-baselined. That
        re-baselining decision is the signal this ticket exists to produce.
        """
        paste = Paste.objects.create(
            id="pygold",
            body="def foo():\n    return 1",
            raw_language="python",
            user=self.user,
        )
        self.assertEqual(
            paste.rendered_body,
            '<div class="paste"><pre><span></span>'
            '<span id="line-1-pygold"><a id="l-1" name="l-1"></a>'
            '<span class="lineno">1</span><span>'
            '<span class="k">def</span> <span class="nf">foo</span>'
            '<span class="p">():</span></span></span>'
            '<span id="line-2-pygold"><a id="l-2" name="l-2"></a>'
            '<span class="lineno">2</span><span>    '
            '<span class="k">return</span> <span class="mi">1</span>'
            "</span></span></pre></div>\n",
        )

    def test_golden_markdown_output(self):
        """Byte-exact markdown rendering, pinned before markdown 2.6 moves to 3.x.

        The sample mixes benign markup with hostile input so the golden output
        also pins the sanitisation: the <script> and <iframe> tags are
        escaped, the onclick handler is stripped, and the javascript: href is
        dropped entirely.
        """
        paste = Paste.objects.create(
            id="goldmd",
            body="# Hello\n"
            "\n"
            "Some **bold** text with a [link](https://example.com/).\n"
            "\n"
            '<script>alert("xss")</script>\n'
            "\n"
            "Click [here](javascript:alert(1)) or "
            '<a href="https://ok.example/" onclick="steal()">there</a>.\n'
            "\n"
            "<iframe><b>kept</b></iframe>",
            raw_language="markdown",
            user=self.user,
        )
        self.assertEqual(
            paste.rendered_body,
            "<h1>Hello</h1>\n"
            "<p>Some <strong>bold</strong> text with a "
            '<a href="https://example.com/" rel="nofollow">link</a>.</p>\n'
            '&lt;script&gt;alert("xss")&lt;/script&gt;\n'
            "\n"
            '<p>Click <a rel="nofollow">here</a> or '
            '<a href="https://ok.example/" rel="nofollow">there</a>.</p>\n'
            "&lt;iframe&gt;<b>kept</b>&lt;/iframe&gt;",
        )

    def test_golden_raw_html_link_gets_nofollow(self):
        """A link written as raw HTML must not bypass the nofollow choke point."""
        paste = Paste.objects.create(
            id="goldraw",
            body='<a href="https://example.com/">raw link</a>',
            raw_language="markdown",
            user=self.user,
        )
        self.assertEqual(
            paste.rendered_body,
            '<p><a href="https://example.com/" rel="nofollow">raw link</a></p>',
        )

    def test_golden_existing_rel_is_preserved(self):
        """An existing rel value survives, with nofollow added alongside."""
        paste = Paste.objects.create(
            id="goldrel",
            body='<a href="https://example.com/" rel="noopener">raw link</a>',
            raw_language="markdown",
            user=self.user,
        )
        self.assertEqual(
            paste.rendered_body,
            '<p><a href="https://example.com/" '
            'rel="noopener nofollow">raw link</a></p>',
        )

    def test_golden_textile_output(self):
        """Byte-exact textile rendering, pinned before textile 2.2 moves to 4.x.

        The hostile subset: textile 2.2.2 replaces the javascript: href with
        a bare "#" and escapes the <script> tag, converting its inner double
        quotes to curly quotes.
        """
        paste = Paste.objects.create(
            id="goldtx",
            body='Some *bold* text with "a link":https://example.com/.\n'
            "\n"
            'Click "here":javascript:alert(1) and '
            '<script>alert("xss")</script>.',
            raw_language="textile",
            user=self.user,
        )
        self.assertEqual(
            paste.rendered_body,
            "\t<p>Some <strong>bold</strong> text with "
            '<a href="https://example.com/" rel="nofollow">a link</a>.</p>\n'
            "\n"
            '\t<p>Click <a href="#" rel="nofollow">here</a> and '
            "&lt;script&gt;alert(&#8220;xss&#8221;)&lt;/script&gt;.</p>",
        )

    def test_markdown_links_get_nofollow(self):
        paste = Paste.objects.create(
            id="nofollow",
            body="A [link](https://example.com/) and an <https://example.org/>.",
            raw_language="markdown",
            user=self.user,
        )
        rendered = paste.rendered_body
        self.assertIn('rel="nofollow"', rendered)
        # Both the inline link and the autolink must carry rel=nofollow.
        self.assertEqual(rendered.count('rel="nofollow"'), 2)


class PasteLanguageTests(TestCase):
    """Tests for the language autodetection."""

    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(
            username="language_user",
            email="language@example.com",
            password="testpass123",
        )

    def test_language_autodetect_confident_guess(self):
        paste = Paste.objects.create(
            id="autogood",
            body="#!/usr/bin/env python\nprint('hi')",
            raw_language="autodetect",
            user=self.user,
        )
        self.assertEqual(paste.language, "python")

    def test_language_autodetect_falls_back_to_text(self):
        paste = Paste.objects.create(
            id="autofail",
            body="asdf qwer zxcv 1234 jkl;",
            raw_language="autodetect",
            user=self.user,
        )
        self.assertEqual(paste.language, "text")


class PasteFilenameTests(TestCase):
    """Tests for the filename property."""

    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(
            username="filename_user",
            email="filename@example.com",
            password="testpass123",
        )

    def test_filename_for_markdown(self):
        paste = Paste.objects.create(
            id="filemd",
            body="# Hello",
            raw_language="markdown",
            user=self.user,
        )
        self.assertEqual(paste.filename, "filemd.md")

    def test_filename_for_textile(self):
        paste = Paste.objects.create(
            id="filetx",
            body="Some text.",
            raw_language="textile",
            user=self.user,
        )
        self.assertEqual(paste.filename, "filetx.txl")

    def test_filename_for_pygments_language(self):
        paste = Paste.objects.create(
            id="filepy",
            body="print('hi')",
            raw_language="python",
            user=self.user,
        )
        self.assertEqual(paste.filename, "filepy.py")


class PasteExpiryTests(TestCase):
    """Tests for has_expired, with main.models.timezone.now frozen."""

    def setUp(self):
        # A fixed instant, so the expiration comparisons below cannot flip
        # on a slow machine.
        self.now = timezone.now()
        self.user = User.objects.create_user(
            username="expiry_user",
            email="expiry@example.com",
            password="testpass123",
        )

    def test_has_expired_by_expiration(self):
        with mock.patch("main.models.timezone.now", return_value=self.now):
            expired = Paste.objects.create(
                id="expired1",
                body="x",
                raw_language="text",
                user=self.user,
                expiration=self.now - timedelta(minutes=1),
            )
            self.assertTrue(expired.has_expired())

            not_yet = Paste.objects.create(
                id="expired2",
                body="x",
                raw_language="text",
                user=self.user,
                expiration=self.now + timedelta(minutes=1),
            )
            self.assertFalse(not_yet.has_expired())

    def test_has_expired_by_max_views(self):
        over_views = Paste.objects.create(
            id="expired3",
            body="x",
            raw_language="text",
            user=self.user,
            views=5,
            max_views=5,
        )
        self.assertTrue(over_views.has_expired())

        under_views = Paste.objects.create(
            id="expired4",
            body="x",
            raw_language="text",
            user=self.user,
            views=4,
            max_views=5,
        )
        self.assertFalse(under_views.has_expired())


class PasteCacheInvalidationTests(TestCase):
    """Tests for the post_save cache invalidation."""

    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(
            username="cache_user",
            email="cache@example.com",
            password="testpass123",
        )

    def test_post_save_invalidation_clears_cached_language_and_rendered_body(self):
        paste = Paste.objects.create(
            id="cach1",
            body="print('hi')",
            raw_language="python",
            user=self.user,
        )
        # Populate both caches.
        self.assertEqual(paste.language, "python")
        paste.rendered_body
        self.assertIsNotNone(cache.get("pastery:paste_cach1_language"))
        self.assertIsNotNone(cache.get("pastery:paste_cach1_rendered_body"))

        paste.title = "A new title"
        paste.save()

        self.assertIsNone(cache.get("pastery:paste_cach1_language"))
        self.assertIsNone(cache.get("pastery:paste_cach1_rendered_body"))

    def test_increment_views_skips_cache_invalidation(self):
        paste = Paste.objects.create(
            id="cach2",
            body="print('hi')",
            raw_language="python",
            user=self.user,
        )
        self.assertEqual(paste.language, "python")
        paste.rendered_body

        paste.increment_views()
        self.assertEqual(paste.views, 1)
        # The flag is reset after the save.
        self.assertFalse(paste._skip_invalidation)
        # View increments must not flush the render caches.
        self.assertIsNotNone(cache.get("pastery:paste_cach2_language"))
        self.assertIsNotNone(cache.get("pastery:paste_cach2_rendered_body"))

        # A regular save afterwards still invalidates.
        paste.title = "A new title"
        paste.save()
        self.assertIsNone(cache.get("pastery:paste_cach2_language"))
        self.assertIsNone(cache.get("pastery:paste_cach2_rendered_body"))
