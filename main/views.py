import base64
import datetime
import json
import re
import time

from annoying.decorators import ajax_request, render_to
from brake.decorators import ratelimit
from captcha.fields import ReCaptchaField
from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login as djlogin, logout as djlogout
from django.contrib.auth.decorators import login_required
from django.contrib.sites.models import Site
from django.core.mail import send_mail
from django.core.signing import Signer
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.translation import ugettext as _
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.http import require_POST
from ipware.ip import get_ip
from raven.contrib.django.raven_compat.models import client


from .models import LANGUAGE_DICT, Paste, STYLES
from utils import send_event  # noqa

User = get_user_model()
LANGUAGE_NAMES = LANGUAGE_DICT.keys()


class PasteForm(forms.ModelForm):
    "The form for a new paste."
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


class EmailForm(forms.Form):
    "The email form for the login page."
    email = forms.EmailField(label="Your email address")


class EmailChangeForm(forms.Form):
    "The email changing form for the account page."
    email = forms.EmailField(label="Your email address")
    confirmation = forms.EmailField(label="Enter your email address again")

    def clean_confirmation(self):
        if self.cleaned_data.get("email") != self.cleaned_data.get("confirmation"):
            raise forms.ValidationError(_("The email addresses must match."))
        return self.cleaned_data["confirmation"]


class UserForm(forms.ModelForm):
    "The user preferences form for the account page."
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
        return redirect("main:home")

    if request.method == 'POST':
        form = PasteForm(request.POST)
        if form.is_valid():
            clean = form.cleaned_data
            data = {}
            data["title"] = clean["title"]
            data["body"] = clean["body"]
            data["raw_language"] = clean["raw_language"]
            data["user_address"] = get_ip(request) if get_ip(request) else ""
            data["views"] = -1

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
            "raw_language": request.GET["lang"] if request.GET.get("lang") in LANGUAGE_NAMES else "autodetect",
        }

        if "expires" in request.GET:
            initial["expires"] = request.GET["expires"]

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
def embed_paste(request, paste_id):
    paste_ids = paste_id.split('+')[:settings.MAX_COMBINED_PASTES]

    pastes = Paste.active.filter(pk__in=paste_ids)
    if not pastes:
        status = 404
        # Show a specific paste.
        pastes = [Paste.active.get(pk="embed404")]
    else:
        status = 200

    data = {
        "pastes": pastes,
        "host": request.GET.get("host", "")
    }
    response = render(request, "embed.html", data, status=status)
    return response


def paste(request, paste_id):
    paste_ids = paste_id.split('+')[:settings.MAX_COMBINED_PASTES]

    # Create a dictionary out of the pastes so we can order them.
    db_pastes = {paste.id: paste for paste in Paste.active.filter(pk__in=paste_ids)}
    for paste in db_pastes.values():
        paste.increment_views()

    pastes = [db_pastes.get(paste_id) for paste_id in paste_ids]

    # If there's only one paste id and it wasn't found, raise a 404.
    if pastes == [None]:
        raise Http404

    return render(request, "paste.html", {
        "pastes": pastes,
        "paste": pastes[0],
        "paste_id": paste_id,
        "has_multiple": len(pastes) > 1
    })


def download_paste(request, paste_id):
    paste = Paste.get_by_id_or_404(paste_id)
    response = HttpResponse(paste.body, content_type="text/plain")
    response["Content-Disposition"] = "attachment; filename=" + paste.filename
    paste.increment_views()
    return response


def raw_paste(request, paste_id):
    paste = Paste.get_by_id_or_404(paste_id)
    response = HttpResponse(paste.body, content_type="text/plain")
    paste.increment_views()
    return response


@require_POST
@ratelimit(method=["POST"], rate="50/d")
@ratelimit(method=["POST"], rate="2/m")
def report_paste(request, paste_id):
    paste = Paste.get_by_id_or_404(paste_id)

    if getattr(request, 'limited', False):
        messages.error(request, _("You're reporting too many pastes. If there's something widespread going on, please contact us directly."))
        return redirect(paste)

    reporter = request.user.username if request.user.is_authenticated() else get_ip(request)
    client.captureMessage("A paste was reported by %s: %s" % (reporter, paste.get_full_url()))
    send_event(reporter, "report_paste", {
        "id": paste.id,
        "url": paste.get_full_url(),
    })
    messages.success(request, _("Thank you for your report. We will investigate as soon as possible."))
    return redirect("main:home")


@require_POST
@login_required
def reset_key(request):
    request.user.reset_key()
    messages.success(request, _("Your API key has been reset."))
    return redirect("main:account")


@require_POST
def delete_paste(request, paste_id):
    paste = Paste.get_by_id_or_404(paste_id)
    if request.user != paste.user:
        messages.error(request, _("That's not your paste, you naughty girl."))
    else:
        send_event(request.user.username, "delete_paste", {
            "id": paste.id,
            "url": paste.get_full_url(),
        })
        paste.delete()
        messages.success(request, _("Your paste has been deleted."))
    return redirect("main:home")


@login_required
@render_to("account.html")
def account(request):
    pastes = []
    if request.method == 'POST':
        pref_form = UserForm(request.POST, instance=request.user)
        email_form = EmailChangeForm(request.POST)
        if request.POST.get("form") == "preferences" and pref_form.is_valid():
            pref_form.save()
            messages.success(request, _("Your settings have been saved."))
            return redirect("main:account")
        elif request.POST.get("form") == "email" and email_form.is_valid():
            email = email_form.cleaned_data["email"].lower().strip()
            if User.objects.filter(email=email).count():
                messages.error(request, _("That email address is already associated with another user. "
                    "Try logging in with it and changing it from the other account if you want to use it"
                    " with this one."))
                return redirect("main:account")
            else:
                request.user.email = email
                request.user.save()
                messages.success(request, _("Your email address has been changed."))
                return redirect("main:account")
        messages.error(request, _("There were errors in the form below."))
    else:
        pref_form = UserForm(instance=request.user)
        email_form = EmailChangeForm(initial={"email": request.user.email})
        pastes = Paste.active.filter(
                user=request.user
            ).order_by('-created')
    return {
        "email_form": email_form,
        "pref_form": pref_form,
        "languages": STYLES,
        "pastes": pastes
    }


@render_to("login.html")
def login(request):
    if request.user.is_authenticated():
        messages.error(request, _("You are already logged in."))
        return redirect("main:home")

    # The user has clicked a login link.
    if request.GET.get("d"):
        user = authenticate(token=request.GET["d"])
        if user is not None:
            djlogin(request, user)
            messages.success(request, _("Login successful."))
            return redirect("main:home")
        messages.error(request, _("The login link was invalid or has expired. Please try to log in again."))

    # The user has submitted the email form.
    if request.method == "POST":
        form = EmailForm(request.POST)
        if form.is_valid():
            messages.success(request, _("Login email sent! Please check your"
                " inbox and click on the link to be logged in."))

            # Create the signed structrure containing the time and email address.
            email = form.cleaned_data["email"].lower().strip()
            data = {"t": int(time.time()), "e": email}
            data = Signer().sign(base64.b64encode(json.dumps(data).encode("utf8")))

            # Send the link by email.
            send_mail(
                    _('Your Pastery login link'),
                    render_to_string("login_email.txt", {"data": data}, request=request),
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False
                    )
            return redirect("main:home")
    else:
        form = EmailForm()
    return {"form": form}


@login_required
def logout(request):
    djlogout(request)
    messages.success(request, _("You have been logged out."))
    return redirect(request.META.get("HTTP_REFERER", "main:home"))


@ajax_request
def oembed(request):
    if request.GET.get("format", "json").lower() != "json":
        return HttpResponse("Format not supported", status=501)

    paste_re = re.search("^https?://.*?/(.*?)(/.*)?$", request.GET.get("url", ""))
    if paste_re:
        paste_id = paste_re.group(1)
    else:
        paste_id = ""
    paste = Paste.get_by_id_or_404(paste_id)

    site = Site.objects.get_current()

    data = {}

    if request.GET.get("embedly"):
        template_name = "embedly_embed_code.html"
        data["width"] = 700
        data["height"] = 400
    else:
        template_name = "embed_code.html"

    data.update({
        "version": "1.0",
        "type": "rich",
        "html": render_to_string(template_name, {"paste": paste}, request=request),
        "provider_name": site.name,
        "provider_url": "https://%s/" % site.domain,
    })

    if paste.title:
        data["title"] = paste.title

    return data
