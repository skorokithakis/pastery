"""pastery URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Import the include() function: from django.conf.urls import url, include
    3. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""

from django.urls import include
from django.urls import re_path
from django.contrib import admin
from django_ratelimit.decorators import ratelimit
from tokenauth import settings as tokenauth_settings
from tokenauth import views as tokenauth_views

from api import urls as api_urls  # noqa
from main import urls as main_urls  # noqa
from pastery.ratelimit import rate_limit_key

urlpatterns = [
    re_path(r"^narnia/", admin.site.urls),
    re_path(r"^api/", include(api_urls)),
    # tokenauth probes for `ratelimit.decorators` (django-ratelimit 3.x) and
    # then `brake.decorators`, and falls back to a no-op decorator when both
    # fail, so it silently loses its per-IP limit with django-ratelimit 4.x
    # (which renamed its module to `django_ratelimit`). This is still true on
    # tokenauth 0.5.5, the last release, so the shim stays: apply the limit
    # it intended to use here. The shim runs before tokenauth's own
    # `require_http_methods`, so it must count POSTs only. tokenauth 0.5.4
    # also dropped the trailing slash from the login URL (and 0.5.1's
    # `^login/$`), so the shim matches both spellings.
    re_path(
        r"^auth/login/?$",
        ratelimit(
            group="tokenauth_login",
            key=rate_limit_key,
            method=["POST"],
            rate=tokenauth_settings.RATELIMIT_RATE,
            block=False,
        )(tokenauth_views.email_post),
    ),
    re_path(r"^auth/", include("tokenauth.urls", namespace="tokenauth")),
    re_path(r"^webauthn/", include("webauthin.urls")),
    re_path(r"^", include(main_urls)),
]
