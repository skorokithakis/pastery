import datetime

from annoying.decorators import render_to
from django import forms
from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect
from django.utils import timezone
from django.utils.translation import ugettext as _

from .models import Paste


@render_to("home.html")
def home(request):
    class PasteForm(forms.ModelForm):
        EXPIRATION = [
            [10, _("Ten minutes")],
            [60, _("An hour")],
            [24 * 60, _("A day")],
            [7 * 24 * 60, _("A week")],
            [14 * 24 * 60, _("Two weeks")],
            [30 * 24 * 60, _("A month")],
        ]
        expires = forms.ChoiceField(choices=EXPIRATION)

        class Meta:
            model = Paste
            fields = ["title", "body", "language"]

    if request.method == 'POST':
        form = PasteForm(request.POST)
        if form.is_valid():
            clean = form.cleaned_data
            data = {}
            data["title"] = clean["title"]
            data["body"] = clean["body"]
            data["language"] = clean["language"]
            data["expiration"] = timezone.now() + datetime.timedelta(
                minutes=int(form.cleaned_data["expires"]))
            if request.user.is_authenticated():
                data["user"] = request.user
            paste = Paste.objects.create(**data)
            messages.success(request, _("Your paste has been created."))
            return redirect(paste)
    else:
        form = PasteForm()
    return {"form": form}


@render_to("paste.html")
def paste(request, paste_id):
    paste = Paste.objects.filter(pk=paste_id).first()

    if not paste or paste.has_expired():
        raise Http404

    return {"paste": paste}
