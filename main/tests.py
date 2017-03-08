from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.utils import timezone
from hypothesis import strategies as st
from hypothesis.extra.django.models import default_value, models

from .models import Paste

User = get_user_model()

UserFactory = models(
        User,
        password=st.just("pass"),
        _style_name=st.just(""),
        api_key=st.just("apikey"),
    )
PasteFactory = models(
        Paste,
        id=default_value,
        expiration=st.integers(min_value=0, max_value=100).map(lambda x: timezone.now() + timedelta(minutes=x)),
        raw_language=default_value,
        views=default_value,
        max_views=default_value,
    )


class SmokeTests(TestCase):
    def setUp(self):
        self.user1 = UserFactory.example()
        self.paste1 = PasteFactory.example()
        self.paste2 = PasteFactory.example()

        # We need this for tests to succeed.
        Paste(id="embed404", body="hi").save()

    def test_urls(self):
        response = self.client.get(reverse("main:home"))
        self.assertEqual(response.status_code, 200)

        response = self.client.get("/nourlthere/")
        self.assertEqual(response.status_code, 404)

    def test_anonymous(self):
        response = self.client.get(reverse("main:home"))
        form = response.context["form"]
        data = form.initial
        data["body"] = "hello!"
        data["work"] = "I'm not a bot, promise"

        response = self.client.post(reverse("main:home"), data, follow=True)
        paste_id = response.context["paste"].id
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"hello!", response.content)
        self.assertIsNone(response.context["paste"].user)

        response = self.client.get(reverse("main:paste", args=[paste_id]))
        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse("main:reset-key"), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, reverse("main:login") + "?next=/account/reset-key/")

        response = self.client.get(reverse("main:embed-paste", args=[paste_id]))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse("main:embed-paste", args=["hi"]))
        self.assertEqual(response.status_code, 404)

        response = self.client.post(reverse("main:delete-paste", args=[paste_id]), follow=True)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse("main:report-paste", args=[paste_id]), follow=True)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse("main:raw-paste", args=[paste_id]))
        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse("main:download-paste", args=[paste_id]))
        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse("main:account"), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, reverse("main:login") + "?next=/account/")

        response = self.client.post(reverse("main:oembed") + "?url=https://hi/" + paste_id)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse("main:oembed") + "?url=https://hi/" + self.paste1.id)
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
        self.assertNotEqual(self.user1.api_key, User.objects.get(id=self.user1.id).api_key)

        response = self.client.post(reverse("main:report-paste", args=[paste_id]), follow=True)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse("main:raw-paste", args=[paste_id]))
        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse("main:download-paste", args=[paste_id]))
        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse("main:delete-paste", args=[paste_id]), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Paste.objects.filter(id=paste_id).count(), 0)

        response = self.client.post(reverse("main:account"), data={"form": "preferences"}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, reverse("main:account"))

        response = self.client.get(reverse("main:logout"), follow=True)
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
