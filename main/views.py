import datetime
import re

import sentry_sdk
from annoying.decorators import ajax_request
from annoying.decorators import render_to
from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.sitemaps import Sitemap
from django.contrib.sites.models import Site
from django.http import Http404
from django.http import HttpResponse
from django.shortcuts import redirect
from django.shortcuts import render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.text import get_valid_filename
from django.utils.translation import gettext as _
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.http import require_POST
from django_ratelimit.decorators import ratelimit

from pastery.ratelimit import get_client_ip
from pastery.ratelimit import is_limited
from pastery.ratelimit import rate_limit_key

from .models import LANGUAGES
from .models import LANGUAGE_DICT
from .models import Paste
from .models import STYLES

User = get_user_model()
LANGUAGE_NAMES = LANGUAGE_DICT.keys()


class StaticViewSitemap(Sitemap):
    priority = 0.5
    changefreq = "daily"

    def items(self):
        return ["/", "/api/", "/about/", "/plugins/", "/login/"]

    def location(self, item):
        return item


def pasteform_factory(user):
    class PasteForm(forms.ModelForm):
        "The form for a new paste."

        EXPIRATION = [
            [10, _("ten minutes")],
            [60, _("an hour")],
            [24 * 60, _("a day")],
            [7 * 24 * 60, _("a week")],
            [14 * 24 * 60, _("two weeks")],
            [30 * 24 * 60, _("a month")],
        ]
        if user.is_authenticated:
            EXPIRATION.append([None, _("never")])

        expires = forms.ChoiceField(
            choices=EXPIRATION,
            initial=30 * 24 * 60,
            label=_("Expires in"),
            required=False,
        )
        raw_language = forms.ChoiceField(choices=LANGUAGES, label=_("Language"))
        work = forms.CharField(required=False)
        other_pastes = forms.CharField(required=False)

        def clean(self):
            cleaned_data = super().clean()
            if cleaned_data.get("work", "") != "I'm not a bot, promise":
                raise forms.ValidationError(
                    _("Please enable Javascript and try pasting again.")
                )
            return cleaned_data

        class Meta:
            model = Paste
            fields = ["title", "body", "raw_language"]

    return PasteForm


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


@ratelimit(
    group="home_daily", key=rate_limit_key, method=["POST"], rate="200/d", block=False
)
@ratelimit(
    group="home_hourly",
    key=rate_limit_key,
    method=["POST"],
    rate="100/h",
    block=False,
)
@ratelimit(
    group="home_minutely",
    key=rate_limit_key,
    method=["POST"],
    rate="20/m",
    block=False,
)
@render_to("home.html")
def home(request):
    if is_limited(request):
        messages.error(request, _("You're pasting too much, please slow down."))
        return redirect("main:home")

    if request.method == "POST":
        if not request.user.is_authenticated:
            messages.error(request, _("To create a new paste, you must log in first."))
            return redirect("main:home")

        form = pasteform_factory(request.user)(request.POST)
        if form.is_valid():
            clean = form.cleaned_data
            data = {}
            data["title"] = clean["title"]
            data["body"] = clean["body"]
            data["raw_language"] = clean["raw_language"]
            data["user"] = request.user
            data["user_address"] = get_client_ip(request)
            data["views"] = -1

            if clean["expires"]:
                data["expiration"] = timezone.now() + datetime.timedelta(
                    minutes=int(clean["expires"])
                )

            paste = Paste.objects.create(**data)

            if clean["other_pastes"]:
                paste_list = re.split(r"\W+", clean["other_pastes"])[
                    -settings.MAX_COMBINED_PASTES + 1 :
                ]
                paste_list.append(paste.id)

                redir_url = reverse("main:paste", args=["+".join(paste_list)])
                redir_url += "#" + paste.id
            else:
                redir_url = reverse("main:paste", args=[paste.id])

            return redirect(redir_url)
    else:
        # See if the user wants to clone a paste.
        initial = {
            "title": request.GET.get("title", ""),
            "body": "",
            "raw_language": (
                request.GET["lang"]
                if request.GET.get("lang") in LANGUAGE_NAMES
                else "autodetect"
            ),
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

        form = pasteform_factory(request.user)(initial=initial)
    return {"form": form}


@xframe_options_exempt
def embed_paste(request, paste_id):
    paste_ids = paste_id.split("+")[: settings.MAX_COMBINED_PASTES]

    # Create a dictionary out of the pastes so we can order them.
    db_pastes = {paste.id: paste for paste in Paste.active.filter(pk__in=paste_ids)}

    # Filter out pastes that the requesting user cannot view
    filtered_pastes = {}
    for paste in db_pastes.values():
        if paste.can_view_paste(request.user):
            filtered_pastes[paste.id] = paste

    for paste in filtered_pastes.values():
        paste.increment_views()

    pastes = [filtered_pastes.get(pasteid) for pasteid in paste_ids]

    # If there's only one paste id and it wasn't found, raise a 404.
    if pastes == [None]:
        status = 404
    else:
        status = 200

    data = {"pastes": pastes, "paste_id": paste_id, "host": request.GET.get("host", "")}
    response = render(request, "embed.html", data, status=status)
    return response


@ratelimit(group="paste_daily", key=rate_limit_key, rate="500/d", block=False)
@ratelimit(group="paste_hourly", key=rate_limit_key, rate="100/h", block=False)
@ratelimit(group="paste_minutely", key=rate_limit_key, rate="20/m", block=False)
def paste(request, paste_id):
    if is_limited(request):
        return HttpResponse(status=429)

    paste_ids = paste_id.strip("+").split("+")[: settings.MAX_COMBINED_PASTES]

    # Create a dictionary out of the pastes so we can order them.
    db_pastes = {paste.id: paste for paste in Paste.active.filter(pk__in=paste_ids)}

    # Filter out pastes that the requesting user cannot view
    filtered_pastes = {}
    for paste in db_pastes.values():
        if paste.can_view_paste(request.user):
            filtered_pastes[paste.id] = paste

    for paste in filtered_pastes.values():
        paste.increment_views()

    pastes = [filtered_pastes.get(pasteid) for pasteid in paste_ids]

    # If there's only one paste id and it wasn't found, raise a 404.
    if pastes == [None]:
        raise Http404

    has_multiple = len(pastes) > 1

    show_full = has_multiple or (
        pastes[0].language != "markdown" and pastes[0].language != "textile"
    )

    if pastes[0] and pastes[0].language == "raw html":
        response = HttpResponse(pastes[0].body, content_type="text/html")
        # Add the CSP header to allow scripts but disable `allow-same-origin` for the sandbox.
        response["Content-Security-Policy"] = (
            "script-src 'unsafe-inline' https:; sandbox allow-scripts"
        )
        # The body is deliberately served unsanitised, so a crawler
        # directive is the only lever: keep raw HTML pastes out of search
        # indexes and stop them passing link equity on.
        response["X-Robots-Tag"] = "noindex, nofollow"
        return response

    return render(
        request,
        "paste.html",
        {
            "pastes": pastes,
            "paste": pastes[0],
            "paste_id": paste_id,
            "has_multiple": has_multiple,
            "show_full": show_full,
        },
    )


@ratelimit(
    group="download_paste_daily",
    key=rate_limit_key,
    rate="500/d",
    block=False,
)
@ratelimit(
    group="download_paste_hourly",
    key=rate_limit_key,
    rate="100/h",
    block=False,
)
@ratelimit(
    group="download_paste_minutely",
    key=rate_limit_key,
    rate="20/m",
    block=False,
)
def download_paste(request, paste_id):
    if is_limited(request):
        return HttpResponse(status=429)

    paste = Paste.get_by_id_or_404(paste_id, request.user)
    response = HttpResponse(paste.body, content_type="text/plain")
    response["Content-Disposition"] = "attachment; filename=" + paste.filename
    paste.increment_views()
    return response


@ratelimit(group="raw_paste_daily", key=rate_limit_key, rate="500/d", block=False)
@ratelimit(group="raw_paste_hourly", key=rate_limit_key, rate="100/h", block=False)
@ratelimit(group="raw_paste_minutely", key=rate_limit_key, rate="20/m", block=False)
def raw_paste(request, paste_id):
    if is_limited(request):
        return HttpResponse(status=429)

    paste = Paste.get_by_id_or_404(paste_id, request.user)
    response = HttpResponse(paste.body, content_type="text/plain; charset=utf-8")
    if paste.title:
        filename = get_valid_filename(paste.title)[:40]
        response["Content-Disposition"] = f'inline; filename="{filename}"'
    paste.increment_views()
    return response


@require_POST
@ratelimit(
    group="report_paste_daily",
    key=rate_limit_key,
    method=["POST"],
    rate="50/d",
    block=False,
)
@ratelimit(
    group="report_paste_minutely",
    key=rate_limit_key,
    method=["POST"],
    rate="2/m",
    block=False,
)
def report_paste(request, paste_id):
    paste = Paste.get_by_id_or_404(paste_id, request.user)

    if is_limited(request):
        messages.error(
            request,
            _(
                "You're reporting too many pastes. If there's something widespread going on, please contact us directly."
            ),
        )
        return redirect(paste)

    reporter = (
        request.user.username
        if request.user.is_authenticated
        else get_client_ip(request)
    )
    sentry_sdk.capture_message(
        "A paste was reported by %s: %s" % (reporter, paste.get_full_url())
    )
    messages.success(
        request,
        _("Thank you for your report. We will investigate as soon as possible."),
    )
    return redirect("main:home")


@require_POST
@login_required
def delete_account(request):
    request.user.delete()
    messages.success(request, _("Your account has been deleted."))
    return redirect("main:home")


@require_POST
@login_required
def reset_key(request):
    request.user.reset_key()
    messages.success(request, _("Your API key has been reset."))
    return redirect("main:account")


@require_POST
def delete_paste(request, paste_id):
    paste = Paste.get_by_id_or_404(paste_id, request.user)
    if request.user != paste.user:
        messages.error(request, _("That's not your paste, you naughty girl."))
    else:
        paste.delete()
        messages.success(request, _("Your paste has been deleted."))
    return redirect("main:home")


@login_required
@render_to("account.html")
def account(request):
    pastes = []
    if request.method == "POST":
        pref_form = UserForm(request.POST, instance=request.user)
        email_form = EmailChangeForm(request.POST)
        if request.POST.get("form") == "preferences" and pref_form.is_valid():
            pref_form.save()
            messages.success(request, _("Your settings have been saved."))
            return redirect("main:account")
        elif request.POST.get("form") == "email" and email_form.is_valid():
            email = email_form.cleaned_data["email"].lower().strip()
            if User.objects.filter(email=email).count():
                messages.error(
                    request,
                    _(
                        "That email address is already associated with another user. "
                        "Try logging in with it and changing it from the other account if you want to use it"
                        " with this one."
                    ),
                )
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
        pastes = Paste.active.filter(user=request.user).order_by("-created")
    return {
        "email_form": email_form,
        "pref_form": pref_form,
        "languages": STYLES,
        "pastes": pastes,
        "keys": request.user.authdata_set.order_by("-last_used_on"),
    }


@render_to("login.html")
def login(request):
    if request.user.is_authenticated:
        messages.error(request, _("You are already logged in."))
        return redirect("main:home")

    return {}


@ajax_request
def oembed(request):
    if request.GET.get("format", "json").lower() != "json":
        return HttpResponse("Format not supported", status=501)

    paste_re = re.search("^https?://.*?/(.*?)(/.*)?$", request.GET.get("url", ""))
    if paste_re:
        paste_id = paste_re.group(1)
    else:
        paste_id = ""
    paste = Paste.get_by_id_or_404(paste_id, request.user)

    site = Site.objects.get_current()

    data = {}

    if request.GET.get("embedly"):
        template_name = "embedly_embed_code.html"
        data["width"] = 700
        data["height"] = 400
    else:
        template_name = "embed_code.html"

    data.update(
        {
            "version": "1.0",
            "type": "rich",
            "html": render_to_string(template_name, {"paste": paste}, request=request),
            "provider_name": site.name,
            "provider_url": "https://%s/" % site.domain,
        }
    )

    if paste.title:
        data["title"] = paste.title

    return data
