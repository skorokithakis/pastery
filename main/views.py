import datetime

from annoying.decorators import render_to
from django.shortcuts import render, get_object_or_404

from .models import Paste


@render_to("home.html")
def home(request):
    return {}


@render_to("paste.html")
def paste(request, paste_id):
    paste = get_object_or_404(Paste, pk=paste_id)
    return {"paste": paste}
