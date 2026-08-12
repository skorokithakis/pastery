---
id: rep-woxjr
status: open
deps: []
links: []
created: 2026-08-12T12:16:20Z
type: chore
priority: 1
assignee: Stavros Korokithakis
---
# Only trust forwarding headers from Cloudflare

Objective: stop the origin trusting client-supplied IP headers.

IPWARE_META_PRECEDENCE_ORDER in pastery/settings.py makes ipware trust HTTP_CF_CONNECTING_IP, HTTP_X_FORWARDED_FOR and six other headers unconditionally, without first checking that REMOTE_ADDR belongs to Cloudflare. pastery/ratelimit.py uses that value as the rate limit bucket key, and the spam blocker keys on it too.

A request that reaches the origin without passing through Cloudflare can therefore rotate CF-Connecting-IP to defeat every rate limit, including the 3/h limit on the login endpoint that sends email, or send another visitor's IP to exhaust that visitor's buckets. Requests that do pass through Cloudflare are safe, because Cloudflare overwrites CF-Connecting-IP itself. So the exposure is direct-to-origin traffic.

This is pre-existing and predates the django-ratelimit migration, which preserved it deliberately.

Two levers, to be decided when this is planned: refuse traffic at the origin unless it comes from a Cloudflare address, or keep trusting the header but only when REMOTE_ADDR is inside Cloudflare's published ranges.

Non-goals: no change to any rate value, and no change to which views are limited.

## Acceptance Criteria

A request that arrives from a non-Cloudflare address with a forged CF-Connecting-IP header cannot pick its own rate limit bucket, and a test proves it.

