from django.test import TestCase, override_settings
from django.core.urlresolvers import reverse


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class SmokeTests(TestCase):
    def test_urls(self):
        response = self.client.get(reverse("main:home"))
        self.assertEqual(response.status_code, 200)

    def test_paste(self):
        response = self.client.get(reverse("main:home"))
        form = response.context["form"]
        data = form.initial
        data["body"] = "hello!"

        response = self.client.post(reverse("main:home"), data, follow=True)
        paste_id = response.context["paste"].id
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"hello!", response.content)

        response = self.client.get(reverse("main:paste", args=[paste_id]))
        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse("main:reset-key"), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, reverse("main:home"))

        response = self.client.get(reverse("main:embed-paste", args=[paste_id]))
        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse("main:delete-paste", args=[paste_id]), follow=True)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse("main:report-paste", args=[paste_id]), follow=True)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse("main:raw-paste", args=[paste_id]))
        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse("main:download-paste", args=[paste_id]))
        self.assertEqual(response.status_code, 200)
