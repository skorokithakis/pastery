---
id: S1-bldcp
status: open
deps: [S1-mkxad]
links: []
created: 2026-08-09T17:56:00Z
type: chore
priority: 1
assignee: Stavros Korokithakis
---
# Replace django-brake with django-ratelimit

Objective: move rate limiting off the dead django-brake onto django-ratelimit 4.x, with no change in observable behaviour.

Affected: nine decorators across main/views.py (four views) and api/views.py (one), plus pastery/brake_backend.py, RATELIMIT_CACHE_BACKEND and RATELIMIT_STATUS_CODE in settings.

Three traps, all silent if you get them wrong:

1. Counter grouping. django-ratelimit derives the counter group from the view's module and name. The stacked decorators on a single view (for example 20/m, 100/h and 200/d on the same view) would therefore all share one bucket. Give every decorator an explicit and distinct group= value.

2. Status code. django-ratelimit's block=True raises Ratelimited, which subclasses PermissionDenied, so Django renders it as 403. brake returns 429 today, via RATELIMIT_STATUS_CODE. Use block=False on every decorator plus one small shared helper that checks request.limited and returns a 429 response. Three views already check 'getattr(request, "limited", False)' by hand; make all of them go through the same helper.

3. Key. The site is behind Cloudflare, so REMOTE_ADDR is a Cloudflare address and django-ratelimit's built-in 'ip' key would put every visitor in one bucket. Use a callable key that resolves the client IP through ipware's get_client_ip, which is what brake_backend.MyBrake did, honouring IPWARE_META_PRECEDENCE_ORDER. get_client_ip can return None; fall back to REMOTE_ADDR in that case rather than to a constant, so that a failure to resolve does not collapse everyone into one bucket.

Delete pastery/brake_backend.py and any settings that no longer apply.

Non-goals: do not change any rate value. Do not add rate limiting to views that do not have it.

## Acceptance Criteria

The 429 tests from the safety-net ticket still pass. A test proves that two decorators with different rates on the same view keep separate counters.


## Notes

**2026-08-09T18:47:12Z**

ready for implementation
