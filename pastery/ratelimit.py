"""Shared helpers for the django-ratelimit based rate limiting."""

from typing import Optional

from django.http import HttpRequest
from ipware import get_client_ip


def rate_limit_key(group: Optional[str], request: HttpRequest) -> Optional[str]:
    """Return the IP to rate limit by.

    The site sits behind Cloudflare, so REMOTE_ADDR is a Cloudflare address
    and django-ratelimit's built-in 'ip' key would put every visitor in one
    bucket. Resolve the real client IP through ipware's get_client_ip, which
    honours IPWARE_META_PRECEDENCE_ORDER, and fall back to REMOTE_ADDR if no
    IP can be resolved, so a resolution failure does not collapse everyone
    into a single bucket.
    """
    ip = get_client_ip(request)[0]
    if ip is None:
        return request.META.get("REMOTE_ADDR")
    return ip


def is_limited(request: HttpRequest) -> bool:
    """Return True if the request was rate limited by the decorators."""
    return getattr(request, "limited", False)
