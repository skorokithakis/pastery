---
id: S1-bskcx
status: closed
deps: [S1-mkxad]
links: []
created: 2026-08-09T17:55:49Z
type: chore
priority: 2
assignee: Stavros Korokithakis
---
# Replace raven with sentry-sdk

Objective: move error reporting from the dead raven client to sentry-sdk.

Work:
- Remove raven from pyproject.toml, remove 'raven.contrib.django.raven_compat' from INSTALLED_APPS, and delete RAVEN_CONFIG.
- Add sentry-sdk with its Django integration. Initialise it in pastery/settings.py from a SENTRY_DSN environment variable. An unset or empty DSN must be a no-op, not an error, because local and CI runs will not have one.
- main/views.py line 315 calls client.captureMessage(...). Replace it with sentry_sdk.capture_message(...), preserving the message and any extra context that was being passed.

Caveats:
- The environment variable changes name, from RAVEN_DSN to SENTRY_DSN. Stavros is adding SENTRY_DSN to Dokku. Do NOT add a fallback that reads RAVEN_DSN.
- Do not enable tracing or profiling. Default error reporting only.

## Acceptance Criteria

Suite green with no DSN set. No reference to raven remains.


## Notes

**2026-08-09T18:47:12Z**

ready for implementation

**2026-08-11T22:31:42Z**

-
