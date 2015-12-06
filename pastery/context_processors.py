from django.conf import settings as sett
from django.contrib.sites.models import Site


def current_site(request):
    return {"current_site": Site.objects.get_current()}


def settings(request):
    return {"settings": sett}
