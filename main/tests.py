# The original SmokeTests have been moved to tests_smoke.py.
# The shadowban tests have been moved to test_shadowban_web.py for better organization.

from django.contrib.auth import get_user_model
from django.test import TestCase
from unittest import mock

from .models import ALIAS_DICT
from .models import LANGUAGES
from .models import Paste
from .models import TOP_LANGUAGES
from .models import get_aliases

User = get_user_model()


class LanguageAliasTests(TestCase):
    """Tests for language alias handling."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="test_user",
            email="test@example.com",
            password="testpass123",
        )

    def test_secondary_alias_normalization(self):
        """Test that secondary aliases like 'js' and 'ahk' are normalized to first aliases."""
        # Create a paste with 'js' (secondary alias for JavaScript).
        paste_js = Paste.objects.create(
            id="testjs",
            title="JavaScript test",
            body="console.log('hello');",
            raw_language="js",
            user=self.user,
        )

        # The language property should normalize 'js' to 'javascript'.
        self.assertEqual(paste_js.language, "javascript")

        # get_language_display should work without raising KeyError.
        display_name = paste_js.get_language_display()
        self.assertIsNotNone(display_name)

        # Create a paste with 'ahk' (secondary alias for AutoHotkey).
        paste_ahk = Paste.objects.create(
            id="testahk",
            title="AutoHotkey test",
            body="MsgBox, Hello",
            raw_language="ahk",
            user=self.user,
        )

        # The language property should normalize 'ahk' to 'autohotkey'.
        self.assertEqual(paste_ahk.language, "autohotkey")

        # get_language_display should work without raising KeyError.
        display_name = paste_ahk.get_language_display()
        self.assertIsNotNone(display_name)


class LanguageListTests(TestCase):
    """Tests for the language dropdown list and alias dictionary."""

    def test_languages_have_no_duplicate_values_or_labels(self):
        """LANGUAGES must not contain duplicate values or duplicate labels.

        This is the check that stops a future Pygments release (which may
        reorder lexer aliases) from resurrecting a duplicate Markdown entry.
        """
        values = [language[0] for language in LANGUAGES]
        labels = [language[1] for language in LANGUAGES]
        self.assertEqual(len(values), len(set(values)))
        self.assertEqual(len(labels), len(set(labels)))

    def test_top_languages_resolve_to_languages(self):
        """Every entry in TOP_LANGUAGES must appear as a value in LANGUAGES.

        The top-languages list is matched against each lexer's first alias, so
        an entry that is only a secondary alias (eg "js" for JavaScript) never
        matches anything and silently drops the language out of the pinned
        group at the top of the dropdown.
        """
        values = [language[0] for language in LANGUAGES]
        for language in TOP_LANGUAGES:
            self.assertIn(language, values)

    def test_markdown_and_markdown_source_are_the_only_markdown_entries(self):
        """The dropdown shows exactly one "Markdown" and one "Markdown (source)"."""
        markdown_entries = [
            language for language in LANGUAGES if language[0].startswith("markdown")
        ]
        self.assertEqual(
            markdown_entries,
            [["markdown", "Markdown"], ["markdown-source", "Markdown (source)"]],
        )

    def test_markdown_and_markdown_source_are_adjacent(self):
        """The two markdown entries sit next to each other in the dropdown."""
        values = [language[0] for language in LANGUAGES]
        self.assertEqual(values.index("markdown") + 1, values.index("markdown-source"))

    def test_markdown_source_passes_through_alias_normalization(self):
        """markdown-source must survive ALIAS_DICT unchanged, and md must still mean markdown."""
        self.assertEqual(ALIAS_DICT["markdown-source"], "markdown-source")
        self.assertEqual(ALIAS_DICT["markdown"], "markdown")
        self.assertEqual(ALIAS_DICT["md"], "markdown")
        self.assertEqual(ALIAS_DICT["textile"], "textile")

    def test_markdown_aliases_survive_reversed_pygments_order(self):
        """The intended mapping holds even if Pygments reorders aliases.

        Pygments 2.8.1 reported the Markdown lexer as ("md", "markdown");
        current versions report ("markdown", "md"). get_aliases() applies its
        hand-written entries last, so the loop's aliases[0] can never override
        them, and "md" must still normalize to "markdown".
        """
        fake_lexers = [
            ("Markdown", ("md", "markdown"), ("md",), ("text/x-markdown",)),
            ("Textile", ("textile",), ("textile",), ("text/x-textile",)),
        ]
        with mock.patch("main.models.get_all_lexers", return_value=fake_lexers):
            alias_dict = get_aliases()
        self.assertEqual(alias_dict["markdown"], "markdown")
        self.assertEqual(alias_dict["md"], "markdown")
        self.assertEqual(alias_dict["markdown-source"], "markdown-source")
        self.assertEqual(alias_dict["textile"], "textile")
