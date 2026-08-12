#!/usr/bin/env python3
"""Check that the Cloudflare ranges in pastery/ratelimit.py match the ranges
Cloudflare publishes today.

Exits zero when they match. Exits one when the committed list has drifted, or
when the published lists cannot be fetched or parsed (with a message that
says the fetch failed, rather than one that implies drift).
"""

import ipaddress
import re
import sys
import time
import urllib.request
from typing import List

CLOUDFLARE_IPV4_URL = "https://www.cloudflare.com/ips-v4"
CLOUDFLARE_IPV6_URL = "https://www.cloudflare.com/ips-v6"

# Meant to be run from the repository root, which is the working directory
# the CI workflow uses.
RATELIMIT_PATH = "pastery/ratelimit.py"

# Retry the fetch a couple of times with a timeout, so one transient network
# failure does not raise a false alarm every week. The retries only help if
# they are not back to back: a blip usually outlasts the instant it takes to
# try again, so pause a few seconds between attempts.
FETCH_ATTEMPTS = 3
FETCH_TIMEOUT_SECONDS = 15
FETCH_RETRY_SLEEP_SECONDS = 5

# Cloudflare answers the default Python-urllib User-Agent with a 403, which
# would fail the weekly run for ever; send a descriptive one instead.
USER_AGENT = "pastery-cloudflare-range-check/1.0"


def fetch(url: str) -> str:
    """Return the body of the URL, retrying a couple of times on failure."""
    last_error: Exception = RuntimeError("fetch was never attempted")
    for attempt in range(FETCH_ATTEMPTS):
        if attempt:
            time.sleep(FETCH_RETRY_SLEEP_SECONDS)
        try:
            request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(
                request, timeout=FETCH_TIMEOUT_SECONDS
            ) as response:
                return response.read().decode("utf-8")
        except Exception as error:
            last_error = error
    raise last_error


def read_committed_ranges(path: str) -> List[str]:
    """Return the committed Cloudflare ranges, read from the source text.

    The module is deliberately not imported: importing it would pull in
    Django and so force the whole pinned dependency set to be installed just
    to read two tuples. Parse the text instead.
    """
    with open(path, encoding="utf-8") as source_file:
        source = source_file.read()

    # Only look between CLOUDFLARE_IPV4_RANGES and the CLOUDFLARE_RANGES
    # alias line, so the ip_network("%s/64", ...) call in rate_limit_key is
    # not mistaken for a committed range.
    start = source.index("CLOUDFLARE_IPV4_RANGES = (")
    end = source.index("CLOUDFLARE_RANGES =")
    ranges_source = source[start:end]

    values = re.findall(r'ipaddress\.ip_network\("([^"]+)"\)', ranges_source)
    # Fail loudly rather than silently pass if the constants are ever
    # reformatted in a way the pattern above no longer matches.
    assert values, (
        "no ipaddress.ip_network(...) values found in ratelimit.py; "
        "the CLOUDFLARE_IPV4/IPV6_RANGES constants must have been reformatted"
    )

    networks: List[str] = []
    for value in values:
        try:
            # Normalise through ip_network so a non-canonical form in the
            # source (e.g. "1.2.3.4/24") still compares equal to the
            # published "1.2.3.0/24".
            network = ipaddress.ip_network(value)
        except ValueError as error:
            raise AssertionError(
                "unparseable network %r in ratelimit.py" % value
            ) from error
        networks.append(str(network))
    return networks


def parse_published_ranges(body: str) -> List[str]:
    """Return the published ranges from a fetched body, normalised.

    Cloudflare publishes one CIDR per line, but a 200 that carries an HTML
    error page or a captive-portal interstitial would split into junk tokens
    instead. Parse every token through ip_network exactly like the committed
    side, so junk fails here as a fetch problem rather than reporting every
    HTML token as a range to add and every real range as a range to remove.
    """
    networks: List[str] = []
    for token in body.split():
        try:
            network = ipaddress.ip_network(token)
        except ValueError as error:
            raise ValueError(
                "unparseable network %r in the published list" % token
            ) from error
        networks.append(str(network))
    # An empty body parses without error but would report every committed
    # range as one to remove, so treat it as a fetch problem too.
    if not networks:
        raise ValueError("the published list was empty")
    return networks


def main() -> int:
    try:
        published = set(parse_published_ranges(fetch(CLOUDFLARE_IPV4_URL))) | set(
            parse_published_ranges(fetch(CLOUDFLARE_IPV6_URL))
        )
    except ValueError as error:
        print(
            "the published Cloudflare list did not look like a list of "
            f"networks ({error}); no drift check performed",
            file=sys.stderr,
        )
        return 1
    except Exception as error:
        print(
            "failed to fetch the Cloudflare published range lists after "
            f"{FETCH_ATTEMPTS} attempts ({error}); no drift check performed",
            file=sys.stderr,
        )
        return 1

    committed = set(read_committed_ranges(RATELIMIT_PATH))
    missing = sorted(published - committed)
    extra = sorted(committed - published)

    if not missing and not extra:
        print("Cloudflare ranges in pastery/ratelimit.py match the published lists.")
        return 0

    print("Cloudflare ranges in pastery/ratelimit.py drifted from the published lists:")
    if missing:
        print(
            "\nAdd these ranges (published by Cloudflare but missing from the tuples):"
        )
        for value in missing:
            print(f'    ipaddress.ip_network("{value}"),')
    if extra:
        print("\nRemove these ranges (in the tuples but no longer published):")
        for value in extra:
            print(f'    ipaddress.ip_network("{value}"),')
    return 1


if __name__ == "__main__":
    sys.exit(main())
