from django.core.management.base import BaseCommand

from main.models import Paste


SPAM_TERMS = {
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
    "donnael.com/",
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
    ".blogkoo.com/",
    ".blogster.com/",
    ".blogdigy.com/",
    ".tblogz.com/",
    ".shotblogs.com/",
    ".canariblogs.com",
    ".angelfire.com",
    "isblog.net/",
}


class Command(BaseCommand):
    help = 'Delete all expired pastes.'

    def handle(self, *args, **options):
        counter = 0
        for term in SPAM_TERMS:
            print("Deleting pastes for %s..." % term)
            deleted = Paste.objects.filter(body__contains=term).delete()
            print("Deleted %s pastes." % deleted[0])
            counter += deleted[0]
        print("Deleted %s pastes." % counter)
