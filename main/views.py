import datetime

from annoying.decorators import render_to
from django import forms
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils import timezone
from django.utils.translation import ugettext as _

from .models import Paste


@render_to("home.html")
def home(request):
    class PasteForm(forms.ModelForm):
        EXPIRATION = [
            [10, _("ten minutes")],
            [60, _("an hour")],
            [24 * 60, _("a day")],
            [7 * 24 * 60, _("a week")],
            [14 * 24 * 60, _("two weeks")],
            [30 * 24 * 60, _("a month")],
            [100 * 365 * 24 * 60, _("never")],
        ]
        expires = forms.ChoiceField(choices=EXPIRATION, initial=24 * 60, label=_("Expires in"))

        class Meta:
            model = Paste
            fields = ["title", "body", "raw_language"]

    if request.method == 'POST':
        form = PasteForm(request.POST)
        if form.is_valid():
            clean = form.cleaned_data
            data = {}
            data["title"] = clean["title"]
            data["body"] = clean["body"]
            data["raw_language"] = clean["raw_language"]
            data["expiration"] = timezone.now() + datetime.timedelta(
                minutes=int(form.cleaned_data["expires"]))
            if request.user.is_authenticated():
                data["user"] = request.user
            paste = Paste.objects.create(**data)
            return redirect(paste)
    else:
        form = PasteForm()
    return {"form": form}


@render_to("paste.html")
def paste(request, paste_id):
    return {"paste": Paste.get_by_id_or_404(paste_id)}


def raw_paste(request, paste_id):
    return HttpResponse(Paste.get_by_id_or_404(paste_id).body, content_type="text/plain")
