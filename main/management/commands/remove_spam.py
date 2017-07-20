import datetime
import re

import requests
from django.conf import settings
from django.core.management.base import BaseCommand

from main.models import Paste


TITLE_TERMS = {
    "watch ",
    "stream",
    "episode",
    "bank",
}

BODY_TERMS = {
    "/successfulmotto",
    "/mightyscenery44",
    "/jbrown316",
    "/genglobal.org",
    "baltec.com/",
    "baltecorporation.com/",
    "h.hatena.ne.jp",
    "-putlocker-",
    "aaaukce.cz",
    "www.victorialostpets.com/",
    "lolita",
    "game-livetvchannel.com/",
    "britishopen2017.co/",
    "grovjobbet.se/",
    "liveonline-itv.com/",
    "lesbenwelt.de/",
    "hatenablog.com/",
    "ghostsfund",
    "undergroundfunds",
    "soci.cf",
    "watchhd-",
    "fullhd-",
    "moviehd-",
    "-hdrip-",
    "movie",
    "hdrrip-",
    "paypal",
    "vodlocker",
    "putlocker",
    "/adfoc.us",
    "/soci.ga",
    "hatelabo.jp/",
    "we are anonymous",
    "transitionnetwork.org/",
    "playbuzz.com/",
    "donnael.com",
    "suomiblog.com/",
    "amoblog.com/",
    "blogzet.com/",
    "alltdesign.com/",
    "bloggersdelight.dk/",
    "indyarocks.com/",
    "logdown.com/",
    "minds.com/",
    "mybjjblog.com/",
    "blogolize.com/",
    "sitepalace.com/",
    "theknot.com/",
    "soundation.com/",
    "blogocial.com/",
    "skyrock.com/",
    "page.tl/",
    "eklablog.com/",
    "blogdon.net/",
    "pointblog.net/",
    "blogminds.com/",
    "vyzon.net/",
    "oximity.com/",
    "vlurn.com/",
    ".blogkoo.com/",
    ".blogster.com/",
    ".blogdigy.com/",
    "animarathon.com/",
    ".tvnet.lv/",
    ".igrcs.com/",
    "dwdstudios.com/",
    ".total-blog.com/",
    ".pitchero.com/",
    ".gamebox.com/",
    ".craftstylish.com/",
    ".shepherdneame.co.uk/",
    ".soclog.se/",
    ".thezenweb.com/",
    ".tblogz.com/",
    ".shotblogs.com/",
    ".canariblogs.com",
    ".angelfire.com",
    ".ampedpages.com/",
    ".pages10.com/",
    ".tinyblogging.com/",
    ".full-design.com/",
    ".endomondo.com/",
    ".vietfun.com/",
    ".goprofanatics.com/",
    ".usgamesfootball.com/",
    ".imperia5x.com/",
    ".redharbinger.com/",
    ".comunidades.net/",
    ".sitepronews.com/",
    ".bitlanders.com/",
    ".openprinting.org/",
    "isblog.net/",
}


def calculate_link_ratio(text):
    if len(text) == 0:
        return 0

    regex = re.compile(r'https?://\S+', re.IGNORECASE)

    total_urls = regex.findall(text)
    url_length = len("".join(total_urls))
    return url_length / len(text)


def ban_ip(ip):
    return True
    print("Banning %s..." % ip)
    url = "https://api.cloudflare.com/client/v4/zones/f1928f8f37c9e76fc7c99a7cc9455702/firewall/access_rules/rules"
    r = requests.post(
        url,
        headers={
            "X-Auth-Email": settings.CLOUDFLARE_EMAIL,
            "X-Auth-Key": settings.CLOUDFLARE_API_KEY
        },
        json={
            "mode": "challenge",
            "configuration": {
                "target": "ip",
                "value": ip
                },
            "notes": "Banned bot: %s" % datetime.date.today().strftime("%Y-%m-%d"),
        }
    )
    return r


class Command(BaseCommand):
    help = 'Delete all expired pastes.'

    def handle(self, *args, **options):
        counter = 0
        for term in BODY_TERMS:
            pastes = Paste.objects.filter(body__contains=term, user=None)
            for paste in pastes:
                ban_ip(paste.user_address)
            deleted = pastes.delete()
            counter += deleted[0]

        for term in TITLE_TERMS:
            pastes = Paste.objects.filter(title__icontains=term, user=None)
            for paste in pastes:
                ban_ip(paste.user_address)
            deleted = pastes.delete()
            counter += deleted[0]

        # Make all userless, non-expiring pastes last a month.
        Paste.objects \
            .filter(user=None) \
            .filter(expiration=None) \
            .update(expiration=datetime.datetime.now() + datetime.timedelta(days=30))

        print("Deleted %s pastes in total." % counter)
