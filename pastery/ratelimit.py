"""Shared helpers for the django-ratelimit based rate limiting."""

from typing import Any
from typing import Optional

from django.http import HttpRequest
from django.http import HttpResponse
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


def limited_response(request: HttpRequest, response: Any = None) -> Any:
    """Return the response to send if the request was rate limited.

    Returns a plain 429 response unless ``response`` is given (e.g. a
    redirect with an error message, or an API error dict). Returns None if
    the request was not limited.
    """
    if getattr(request, "limited", False):
        return response if response is not None else HttpResponse(status=429)
    return None
