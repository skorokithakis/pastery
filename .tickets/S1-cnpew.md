---
id: S1-cnpew
status: closed
deps: [S1-nweul]
links: []
created: 2026-08-09T17:56:22Z
type: chore
priority: 1
assignee: Stavros Korokithakis
---
# Land the forward-compatible Django changes while still on 2.0

Objective: make every change that Django 4.x will demand but that Django 2.0 already accepts, so the version hops carry less risk.

- ugettext and ugettext_lazy become gettext and gettext_lazy: main/views.py line 23, main/admin.py line 3, main/models.py line 26.
- django.conf.urls.url becomes django.urls.re_path: pastery/urls.py, main/urls.py, api/urls.py. Keep the regex strings exactly as they are; do not convert to path(). Note that one entry passes the unanchored string 'sitemap.xml' rather than a regex; keep it unanchored so the matching behaviour does not change.
- '{% load staticfiles %}' becomes '{% load static %}' in main/templates/404.html, 500.html, embed.html, paste.html and home.html. The staticfiles tag library was removed in Django 3.0.
- The database ENGINE 'django.db.backends.postgresql_psycopg2' becomes 'django.db.backends.postgresql' in both database blocks in pastery/settings.py, including the production one. Delete the stale trailing comment listing backend names.
- Add SECURE_PROXY_SSL_HEADER set to the X-Forwarded-Proto header, and CSRF_TRUSTED_ORIGINS listing the https origins for pastery.net and www.pastery.net. Add a comment explaining why: Dokku's nginx terminates TLS and proxies plain HTTP to the container, so without this request.is_secure() is False for every request, and Django 4.0's Origin check would then reject every POST on the live site.

Caveat: SECURE_PROXY_SSL_HEADER changes live behaviour as soon as it deploys, because request.is_secure() starts returning True. Confirm nothing in the codebase depends on it being False, and confirm SECURE_SSL_REDIRECT is not set, so there is no redirect loop.

Non-goals: no dependency changes, no Django version change.

## Acceptance Criteria

No occurrence of ugettext, conf.urls.url, load staticfiles or postgresql_psycopg2 remains outside migrations. Suite green.


## Notes

**2026-08-09T18:47:12Z**

ready for implementation

**2026-08-10T07:18:03Z**

Extra occurrence of the old ENGINE alias to rename here. S1-sfqqx added a heredoc in .github/workflows/ci.yml that writes pastery/local_settings.py for the CI Postgres service, and it uses 'django.db.backends.postgresql_psycopg2'. So this ticket has three places to change, not two: both blocks in pastery/settings.py plus that heredoc. Harmless today, but it must be gone before the 3.2 rung.
