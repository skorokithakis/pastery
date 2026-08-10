# The original SmokeTests have been moved to tests_smoke.py.
# The shadowban tests have been moved to test_shadowban_web.py for better organization.

from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import Paste

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
