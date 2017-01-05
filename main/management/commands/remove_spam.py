import re

from django.core.management.base import BaseCommand

from main.models import Paste


TITLE_TERMS = {
    "watch ",
    "stream",
    "episode",
}

BODY_TERMS = {
    "/successfulmotto",
    "/mightyscenery44",
    "/jbrown316",
    "/genglobal.org",
    "h.hatena.ne.jp",
    "-putlocker-",
    "aaaukce.cz",
    "www.victorialostpets.com/",
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


class Command(BaseCommand):
    help = 'Delete all expired pastes.'

    def handle(self, *args, **options):
        counter = 0
        for term in BODY_TERMS:
            deleted = Paste.objects.filter(body__contains=term, user=None).delete()
            counter += deleted[0]

        for term in TITLE_TERMS:
            deleted = Paste.objects.filter(title__icontains=term, user=None).delete()
            counter += deleted[0]

        for paste in Paste.objects.filter(user=None):
            ratio = calculate_link_ratio(paste.body)
            if ratio > 0.2:
                paste.delete()
                counter += 1
        print("Deleted %s pastes in total." % counter)
