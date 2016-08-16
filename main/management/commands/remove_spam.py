from django.core.management.base import NoArgsCommand
from django.utils import timezone

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
    "hdrrip-",
    "paypal",
    "/adfoc.us",
    "/soci.ga",
]


class Command(NoArgsCommand):
    help = 'Delete all expired pastes.'

    def handle(self, *args, **options):
        counter = 0
        for paste in Paste.active.all():
            haystack = paste.body.lower()
            for spam_term in SPAM_TERMS:
                if spam_term in haystack:
                    print("Deleting %s..." % paste.id)
                    paste.delete()
                    counter += 1
                    break
        print("Deleted %s pastes." % counter)
