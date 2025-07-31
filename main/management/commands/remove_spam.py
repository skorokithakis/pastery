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
    return url_length / len(re.findall(r"\S", text))


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
            "--regex", type=str, help="Delete all links whose title matches REGEX"
        )
        parser.add_argument(
            "--link-ratio",
            type=float,
            help="Delete all links with a link ratio higher than RATIO",
        )

    def handle(self, *args, **options):
        term_setting = Setting.objects.filter(key="SPAM_TERMS").first()
        counter = 0

        ratio_threshold = options["link_ratio"]
        regex = options["regex"]

        # Get spam terms if configured
        spam_terms = None
        if term_setting:
            spam_terms = json.loads(term_setting.value)

        for paste in Paste.objects.filter(spam_processed=False):
            is_spam = False

            # Check regex if provided
            if regex and re.search(regex, paste.title, re.IGNORECASE):
                print("Deleting %s (matches regex)..." % paste)
                is_spam = True

            # Check link ratio if provided and paste is long enough
            if not is_spam and ratio_threshold and len(paste.body) >= 50:
                ratio = calculate_link_ratio(paste.body)
                print(f"{paste.id} {ratio}")
                if ratio >= ratio_threshold:
                    print("Deleting %s (link ratio: %s)..." % (paste, ratio))
                    is_spam = True

            # Check spam terms if configured
            if not is_spam and spam_terms:
                # Check body terms
                for term in spam_terms.get("body", []):
                    if term in paste.body:
                        print("Deleting %s (contains spam term in body)..." % paste)
                        is_spam = True
                        ban_ip(paste.user_address)
                        break

                # Check title terms if not already marked as spam
                if not is_spam:
                    for term in spam_terms.get("title", []):
                        if term.lower() in paste.title.lower():
                            print(
                                "Deleting %s (contains spam term in title)..." % paste
                            )
                            is_spam = True
                            ban_ip(paste.user_address)
                            break

            # Delete if spam, otherwise mark as processed
            if is_spam:
                paste.delete()
                counter += 1
            else:
                paste.spam_processed = True
                paste.save()

        print("Deleted %s pastes in total." % counter)
