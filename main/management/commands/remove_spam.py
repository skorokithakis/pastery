import datetime
import json
import re

import requests
from django.conf import settings
from django.core.management.base import BaseCommand

from main.models import Paste
from main.models import Setting


def calculate_link_ratio(text):
    if len(text) == 0:
        return 0

    regex = re.compile(r"https?://\S+", re.IGNORECASE)

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
            "X-Auth-Key": settings.CLOUDFLARE_API_KEY,
        },
        json={
            "mode": "challenge",
            "configuration": {"target": "ip", "value": ip},
            "notes": "Banned bot: %s" % datetime.date.today().strftime("%Y-%m-%d"),
        },
    )
    return r


class Command(BaseCommand):
    help = "Delete all expired pastes."

    def add_arguments(self, parser):
        # Named (optional) arguments
        parser.add_argument(
            "--link-ratio",
            type=float,
            help="Delete all links with a link ratio higher than RATIO",
        )

    def handle(self, *args, **options):
        term_setting = Setting.objects.filter(key="SPAM_TERMS").first()

        ratio_threshold = options["link_ratio"]

        counter = 0
        if ratio_threshold:
            for paste in Paste.objects.filter(user=None):
                if len(paste.body) < 50:
                    continue

                ratio = calculate_link_ratio(paste.body)
                if ratio > ratio_threshold:
                    print("Deleting %s (%s)..." % (paste, ratio))
                    paste.delete()
                    counter += 1

        if not term_setting:
            print("No terms found, quitting...")
            return

        terms = json.loads(term_setting.value)
        body_terms = terms["body"]
        title_terms = terms["title"]

        for term in body_terms:
            pastes = Paste.objects.filter(body__contains=term, user=None)
            for paste in pastes:
                ban_ip(paste.user_address)
            deleted = pastes.delete()
            counter += deleted[0]

        for term in title_terms:
            pastes = Paste.objects.filter(title__icontains=term, user=None)
            for paste in pastes:
                ban_ip(paste.user_address)
            deleted = pastes.delete()
            counter += deleted[0]

        # Make all userless, non-expiring pastes last a month.
        Paste.objects.filter(user=None).filter(expiration=None).update(
            expiration=datetime.datetime.now() + datetime.timedelta(days=30)
        )

        print("Deleted %s pastes in total." % counter)
