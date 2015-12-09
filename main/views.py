import datetime

from annoying.decorators import render_to
from brake.decorators import ratelimit
from captcha.fields import ReCaptchaField
from django import forms
from django.db.models import Count
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, logout as djlogout
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from django.shortcuts import redirect
from django.utils import timezone
from django.utils.translation import ugettext as _
from django.views.decorators.clickjacking import xframe_options_exempt
from ipware.ip import get_ip
from raven.contrib.django.raven_compat.models import client


from .models import Paste, STYLES, LANGUAGE_DICT

User = get_user_model()
LANGUAGE_NAMES = LANGUAGE_DICT.keys()


class PasteForm(forms.ModelForm):
    EXPIRATION = [
        [10, _("ten minutes")],
        [60, _("an hour")],
        [24 * 60, _("a day")],
        [7 * 24 * 60, _("a week")],
        [14 * 24 * 60, _("two weeks")],
        [30 * 24 * 60, _("a month")],
        [None, _("never")],
    ]
    expires = forms.ChoiceField(choices=EXPIRATION, initial=24 * 60, label=_("Expires in"), required=False)
    work = forms.CharField(required=False)
    if settings.ENABLE_CAPTCHA:
        captcha = ReCaptchaField()

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("work", ""):
            raise forms.ValidationError(_("Please stop being a bot and try pasting again."))
        return cleaned_data

    class Meta:
        model = Paste
        fields = ["title", "body", "raw_language"]


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["_style_name"]


@ratelimit(method=["POST"], rate="1000/d")
@ratelimit(method=["POST"], rate="500/h")
@ratelimit(method=["POST"], rate="20/m")
@render_to("home.html")
def home(request):
    if getattr(request, 'limited', False):
        messages.error(request, _("You're pasting too much, please slow down."))
        return redirect(home)

    if request.method == 'POST':
        form = PasteForm(request.POST)
        if form.is_valid():
            clean = form.cleaned_data
            data = {}
            data["title"] = clean["title"]
            data["body"] = clean["body"]
            data["raw_language"] = clean["raw_language"]
            data["user_address"] = get_ip(request) or ""

            if clean["expires"]:
                data["expiration"] = timezone.now() + datetime.timedelta(minutes=int(clean["expires"]))

            if request.user.is_authenticated():
                data["user"] = request.user

            paste = Paste.objects.create(**data)
            return redirect(paste)
    else:
        # See if the user wants to clone a paste.
        initial = {
            "title": request.GET.get("title", ""),
            "body": "",
            "raw_language": request.GET["lang"] if request.GET.get("lang") in LANGUAGE_NAMES else "autodetect"
        }
        clone = request.GET.get("clone")
        if clone:
            paste = Paste.active.filter(pk=clone).first()
            if paste:
                initial = {
                    "title": paste.title,
                    "body": paste.body,
                    "raw_language": paste.language,
                }

        form = PasteForm(initial=initial)
    return {"form": form}


@xframe_options_exempt
@render_to("embed.html")
def embed_paste(request, paste_id):
    return {
        "paste": Paste.get_by_id_or_404(paste_id),
        "host": request.GET.get("host", "")
    }


@render_to("paste.html")
def paste(request, paste_id):
    return {"paste": Paste.get_by_id_or_404(paste_id)}


def raw_paste(request, paste_id):
    return HttpResponse(Paste.get_by_id_or_404(paste_id).body, content_type="text/plain")


@require_POST
@ratelimit(method=["POST"], rate="50/d")
@ratelimit(method=["POST"], rate="2/m")
def report_paste(request, paste_id):
    paste = Paste.get_by_id_or_404(paste_id)

    if getattr(request, 'limited', False):
        messages.error(request, _("You're reporting too many paste. If there's something widespread going on, please contact us directly."))
        return redirect(paste)

    reporter = request.user.username if request.user.is_authenticated() else get_ip(request)
    client.captureMessage("A paste was reported by %s: %s" % (reporter, paste.get_full_url()))
    messages.success(request, _("Thank you for your report. We will investigate as soon as possible."))
    return redirect(home)


@require_POST
def delete_paste(request, paste_id):
    paste = Paste.get_by_id_or_404(paste_id)
    if request.user != paste.user:
        messages.error(request, _("That's not your paste, you naughty girl."))
    else:
        paste.delete()
        messages.success(request, _("Your paste has been deleted."))
    return redirect(home)


@render_to("account.html")
def account(request):
    if request.user.is_anonymous():
        messages.error(request, _("You need to log in first."))
        return redirect(home)

    pastes = []
    if request.method == 'POST':
        form = UserForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, _("Your settings have been saved."))
            return redirect(account)
    else:
        form = UserForm(instance=request.user)
        pastes = Paste.active.filter(
                user=request.user
            ).annotate(
                null_expiration=Count('expiration')
            ).order_by('-null_expiration', 'expiration')
    return {"form": form, "languages": STYLES, "pastes": pastes}


def logout(request):
    djlogout(request)
    messages.success(request, _("You have been logged out."))
    return redirect(request.META.get("HTTP_REFERER", home))
