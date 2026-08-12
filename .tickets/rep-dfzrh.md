---
id: rep-dfzrh
status: closed
deps: []
links: []
created: 2026-08-12T13:53:13Z
type: chore
priority: 1
assignee: Stavros Korokithakis
---
# Resolve the client IP from the Cloudflare trust chain, and bucket IPv6 by /64

Objective: implement the two decisions recorded on rep-woxjr. Replace django-ipware with a small local resolver that only trusts CF-Connecting-IP when the request really came from Cloudflare, and make the rate limit bucket for an IPv6 client its /64 rather than its /128.

Read rep-woxjr for the threat description and the planning note before you start.

Scope:
- pastery/ratelimit.py holds both functions. No new module.
  get_client_ip(request) -> str returns the trusted client IP, full and untruncated. rate_limit_key(group, request) -> str returns that value for IPv4 and the /64 network for IPv6.
- The Cloudflare ranges live as a module-level constant in the same file. Fetch the current lists from https://www.cloudflare.com/ips-v4 and https://www.cloudflare.com/ips-v6 at implementation time, commit them, and put the source URLs and the date in a comment above them. Both families are needed: the AAAA records are proxied too.
- Delete IPWARE_META_PRECEDENCE_ORDER from pastery/settings.py, drop django-ipware from pyproject.toml, and re-lock with uv. django-ipware is a direct dependency only, nothing else pulls it in.
- Move the three remaining ipware call sites onto the new function: main/views.py (paste user_address, and the reporter in report_paste) and api/views.py (paste user_address). They all currently do get_client_ip(request)[0]; the new function returns a plain string, so the "[0] if ... else \"\"" dance goes away.

Resolution rules:
- Peer = the right-most entry of X-Forwarded-For, falling back to REMOTE_ADDR when the header is absent, which is the runserver and test-client case.
- If the peer is inside the Cloudflare ranges, the client IP is CF-Connecting-IP. If that header is missing or does not parse, use the peer.
- Otherwise the client IP is the peer itself. A forged CF-Connecting-IP from a non-Cloudflare peer must be ignored entirely.
- Return "" if nothing resolves. Never return None; three call sites want a string.

Non-goals: no change to any rate value, no change to which views are limited, no change to IPv4 bucket width, and no truncation of the value stored in Paste.user_address or reported to Sentry. Those keep the full address. Only the rate limit key is collapsed to a /64.

Caveats:
- Use the stdlib ipaddress module. Both ip_address() and ip_network() raise ValueError on junk, and the REMOTE_ADDR fallback and CF-Connecting-IP are not guaranteed well-formed. Handle it; do not let a malformed header 500 the request.
- Normalise IPv4-mapped IPv6 (::ffff:1.2.3.4) to plain IPv4 before you compare or truncate, otherwise such an address gets a nonsense /64 bucket.
- The docstring in pastery/ratelimit.py says REMOTE_ADDR is a Cloudflare address. That is wrong. Correct it while you are there.
- main/tests_networking.py imports ipware directly and ClientIPTests asserts ipware behaviour. Rewrite those two tests against the new function. test_cf_connecting_ip_gets_its_own_bucket also needs a Cloudflare X-Forwarded-For added, or it will stop proving what it claims.

## Acceptance Criteria

Tests, using real addresses from the committed ranges rather than patched settings:
- Two requests from the same non-Cloudflare peer with different forged CF-Connecting-IP values land in the same bucket. This is the rep-woxjr criterion.
- CF-Connecting-IP is honoured when the peer is a Cloudflare address.
- Two IPv6 clients in one /64 share a bucket; two in different /64s do not.
Suite green.


## Notes

**2026-08-12T13:53:17Z**

ready for implementation
