# Tests for the remove_spam management command and its link-ratio helper.
# The command runs daily against the whole Paste table (spam_processed=False),
# so the delete/keep decisions below are pinned to stop a regression from
# silently deleting real pastes.

from unittest import mock

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

from .management.commands.remove_spam import calculate_link_ratio
from .models import Paste

User = get_user_model()


class CalculateLinkRatioTests(TestCase):
    def test_empty_text_scores_zero(self):
        self.assertEqual(calculate_link_ratio(""), 0)

    def test_whitespace_only_text_scores_zero(self):
        self.assertEqual(calculate_link_ratio(" \n\t \n"), 0)

    def test_pure_urls_score_one(self):
        body = "https://spam.example.com/a/ https://spam.example.com/b/"
        self.assertEqual(calculate_link_ratio(body), 1.0)

    def test_mixed_text_scores_url_share_of_non_whitespace(self):
        body = "https://spam.example.com/ hello world"
        # 25 URL characters out of 35 non-whitespace characters.
        self.assertAlmostEqual(calculate_link_ratio(body), 25 / 35)


class RemoveSpamCommandTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="remove_spam_user",
            email="removespam@example.com",
            password="testpass123",
        )
        # A pure-URL body comfortably over the default --min-length of 500.
        self.spam_body = " ".join(["https://spam.example.com/"] * 21)
        self.long_plain_body = "regular prose with no links at all. " * 40

    def make_paste(self, paste_id, body, spam_processed=False):
        return Paste.objects.create(
            id=paste_id,
            body=body,
            raw_language="text",
            user=self.user,
            spam_processed=spam_processed,
        )

    def test_spammy_long_paste_is_deleted(self):
        paste = self.make_paste("spam1", self.spam_body)
        call_command("remove_spam", link_ratio=0.98)
        self.assertFalse(Paste.objects.filter(id=paste.id).exists())

    def test_normal_long_paste_is_kept_and_marked_processed(self):
        paste = self.make_paste("keep1", self.long_plain_body)
        call_command("remove_spam", link_ratio=0.98)
        paste.refresh_from_db()
        self.assertTrue(paste.spam_processed)

    def test_body_shorter_than_min_length_is_never_deleted_on_ratio_path(self):
        # A single pasted URL must survive: it scores 1.0, but the length
        # gate keeps the ratio path from ever looking at it.
        paste = self.make_paste("short1", "https://spam.example.com/single/")
        call_command("remove_spam", link_ratio=0.98)
        paste.refresh_from_db()
        self.assertTrue(paste.spam_processed)

    def test_min_length_option_overrides_default(self):
        paste = self.make_paste("short2", "https://spam.example.com/single/")
        call_command("remove_spam", link_ratio=0.98, min_length=10)
        self.assertFalse(Paste.objects.filter(id=paste.id).exists())

    def test_whitespace_only_long_paste_does_not_crash_and_is_not_deleted(self):
        # Exactly at the default --min-length, so the ratio path runs on a
        # body with no non-whitespace characters.
        paste = self.make_paste("ws1", " " * 500)
        call_command("remove_spam", link_ratio=0.98)
        paste.refresh_from_db()
        self.assertTrue(paste.spam_processed)
        self.assertTrue(Paste.objects.filter(id=paste.id).exists())

    def test_link_ratio_zero_is_a_real_threshold(self):
        # With a truthiness check, --link-ratio 0 would disable the ratio
        # path entirely; "is not None" makes it delete everything over the
        # length gate.
        paste = self.make_paste("zero1", self.long_plain_body)
        call_command("remove_spam", link_ratio=0)
        self.assertFalse(Paste.objects.filter(id=paste.id).exists())

    def test_link_ratio_zero_still_respects_min_length(self):
        paste = self.make_paste("zero2", "https://spam.example.com/single/")
        call_command("remove_spam", link_ratio=0)
        paste.refresh_from_db()
        self.assertTrue(paste.spam_processed)

    def test_already_processed_pastes_are_not_rescanned(self):
        paste = self.make_paste("done1", self.spam_body, spam_processed=True)
        call_command("remove_spam", link_ratio=0.98)
        self.assertTrue(Paste.objects.filter(id=paste.id).exists())

    def test_keep_path_only_saves_spam_processed(self):
        # update_fields must not be dropped: a full save would rewrite the
        # body and every other field on each daily run.
        self.make_paste("save1", self.long_plain_body)
        update_fields_seen = []
        original_save = Paste.save

        def recording_save(self, *args, **kwargs):
            update_fields_seen.append(kwargs.get("update_fields"))
            return original_save(self, *args, **kwargs)

        with mock.patch.object(Paste, "save", recording_save):
            call_command("remove_spam", link_ratio=0.98)
        self.assertEqual(update_fields_seen, [["spam_processed"]])
