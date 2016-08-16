from django.core.management.base import BaseCommand

from main.models import Paste


SPAM_TERMS = [
    "/successfulmotto",
    "/mightyscenery44",
    "/jbrown316",
    "/genglobal.org",
    "http://h.hatena.ne.jp",
    "-putlocker-",
    "aaaukce.cz",
    "http://www.victorialostpets.com/",
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
    "sitepalace.com/",
    "theknot.com/",
    "soundation.com/",
]


class Command(BaseCommand):
    help = 'Delete all expired pastes.'

    def handle(self, *args, **options):
        counter = 0
        for paste in Paste.objects.all():
            haystack = paste.body.lower()
            for spam_term in SPAM_TERMS:
                if spam_term in haystack:
                    print("Deleting %s because of \"%s\"..." % (paste.id, spam_term))
                    paste.delete()
                    counter += 1
                    break
        print("Deleted %s pastes." % counter)
