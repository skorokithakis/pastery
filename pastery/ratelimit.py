"""Shared helpers for the django-ratelimit based rate limiting."""

import ipaddress
from typing import Optional
from typing import Union

from django.http import HttpRequest

# Cloudflare's published edge ranges, fetched 2026-08-12 from
# https://www.cloudflare.com/ips-v4 and https://www.cloudflare.com/ips-v6.
# Both families are needed: the AAAA records are proxied too.
CLOUDFLARE_IPV4_RANGES = (
    ipaddress.ip_network("173.245.48.0/20"),
    ipaddress.ip_network("103.21.244.0/22"),
    ipaddress.ip_network("103.22.200.0/22"),
    ipaddress.ip_network("103.31.4.0/22"),
    ipaddress.ip_network("141.101.64.0/18"),
    ipaddress.ip_network("108.162.192.0/18"),
    ipaddress.ip_network("190.93.240.0/20"),
    ipaddress.ip_network("188.114.96.0/20"),
    ipaddress.ip_network("197.234.240.0/22"),
    ipaddress.ip_network("198.41.128.0/17"),
    ipaddress.ip_network("162.158.0.0/15"),
    ipaddress.ip_network("104.16.0.0/13"),
    ipaddress.ip_network("104.24.0.0/14"),
    ipaddress.ip_network("172.64.0.0/13"),
    ipaddress.ip_network("131.0.72.0/22"),
)

CLOUDFLARE_IPV6_RANGES = (
    ipaddress.ip_network("2400:cb00::/32"),
    ipaddress.ip_network("2606:4700::/32"),
    ipaddress.ip_network("2803:f800::/32"),
    ipaddress.ip_network("2405:b500::/32"),
    ipaddress.ip_network("2405:8100::/32"),
    ipaddress.ip_network("2a06:98c0::/29"),
    ipaddress.ip_network("2c0f:f248::/32"),
)

CLOUDFLARE_RANGES = CLOUDFLARE_IPV4_RANGES + CLOUDFLARE_IPV6_RANGES

Address = Union[ipaddress.IPv4Address, ipaddress.IPv6Address]


def _is_cloudflare(address: Address) -> bool:
    """Return True if the address falls inside a published Cloudflare range."""
    return any(address in network for network in CLOUDFLARE_RANGES)


def _parse_address(value: Optional[str]) -> Optional[Address]:
    """Parse a header value into an address, or return None on junk.

    IPv4-mapped IPv6 addresses (::ffff:1.2.3.4) are normalised to plain
    IPv4 so that Cloudflare range checks and /64 truncation see the address
    the client means rather than a nonsense v6 one.
    """
    if value is None:
        return None
    try:
        address = ipaddress.ip_address(value)
    except ValueError:
        return None
    if address.version == 6 and address.ipv4_mapped is not None:
        return address.ipv4_mapped
    return address


def _peer_address(request: HttpRequest) -> Optional[Address]:
    """Return the address of the immediate peer, as nginx saw it.

    Dokku's nginx always overwrites X-Forwarded-For with its own peer
    ($remote_addr), so the container sees exactly one value and a client
    cannot forge it: the right-most entry is the trust anchor. When the
    header is absent we fall back to REMOTE_ADDR, which is the runserver
    and test-client case. Inside the container REMOTE_ADDR is the Docker
    gateway, not a Cloudflare address, so it can only be trusted when the
    request really came through nginx.
    """
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return _parse_address(xff.split(",")[-1].strip())
    return _parse_address(request.META.get("REMOTE_ADDR"))


def get_client_ip(request: HttpRequest) -> str:
    """Return the client IP, full and untruncated.

    Only requests that really came through Cloudflare are trusted to carry
    a CF-Connecting-IP header: the header is honoured only when the peer is
    inside Cloudflare's published ranges. Otherwise it is ignored entirely,
    so a direct-to-origin attacker cannot pick their own rate limit bucket
    or send someone else's IP. Returns "" if nothing resolves.
    """
    peer = _peer_address(request)
    if peer is None:
        return ""
    if _is_cloudflare(peer):
        connecting_ip = _parse_address(request.META.get("HTTP_CF_CONNECTING_IP"))
        if connecting_ip is not None:
            return str(connecting_ip)
    return str(peer)


def rate_limit_key(group: Optional[str], request: HttpRequest) -> str:
    """Return the IP to rate limit by: the client IP, IPv6 in its /64.

    IPv4 clients are bucketed by their full address. IPv6 clients share a
    bucket with everyone in their /64, so rotating addresses within a /64
    cannot defeat an IP-based limit.
    """
    ip = get_client_ip(request)
    try:
        address = ipaddress.ip_address(ip)
    except ValueError:
        return ip
    if address.version == 6:
        return str(ipaddress.ip_network("%s/64" % ip, strict=False))
    return ip


def is_limited(request: HttpRequest) -> bool:
    """Return True if the request was rate limited by the decorators."""
    return getattr(request, "limited", False)
