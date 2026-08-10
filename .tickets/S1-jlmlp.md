---
id: S1-jlmlp
status: closed
deps: [S1-sfqqx]
links: []
created: 2026-08-09T17:55:27Z
type: chore
priority: 1
assignee: Stavros Korokithakis
---
# Widen the test safety net before the upgrade

Objective: add tests where the upgrade is going to do damage, before it does it. Coverage is 33 percent overall, main/models.py is at 28 and main/admin.py at 0.

Add to main/models.py tests, targeting roughly 70 percent coverage of that file:
- rendered_body for all three paths: markdown, textile, and the Pygments highlighter.
- Golden output tests: one fixed markdown sample and one fixed textile sample, asserting the exact rendered HTML.
- A test that links in rendered markdown carry rel=nofollow.
- language autodetect: a confident guess, and the fall back to 'text' when nothing matches the 5 percent confidence floor.
- filename for markdown, for textile, and for a Pygments language.
- has_expired for both the expiration path and the max_views path.
- The post_save cache invalidation, including the _skip_invalidation flag used by increment_views.

Add to main/admin.py tests:
- Load each registered changelist as a superuser and assert 200.
- Exercise ShadowbannedUserFilter for both the yes and the no value.

Add two cross-cutting tests:
- Client IP: assert that the configured IPWARE_META_PRECEDENCE_ORDER is honoured, so HTTP_CF_CONNECTING_IP wins over REMOTE_ADDR. The rate limiter and the spam blocker both key on this, and django-ipware is going from 2.1 to 7.
- Rate limiting: assert a limited request gets HTTP 429. Cover one view that uses block=True and one that uses block=False.

Non-goals: do not chase coverage on urls.py or migrations. Do not refactor the code under test; this ticket only adds tests.

## Design

The golden output tests are the point of this ticket. markdown 2.6 to 3.x, bleach 3.2 to 6.x and textile 2.2 to 4.x all change the generated HTML. Without a byte-exact assertion, that change is invisible and lands silently on every paste on the site.

## Acceptance Criteria

Coverage of main/models.py is around 70 percent or better. main/admin.py is exercised at least at changelist level. All tests pass.


## Notes

**2026-08-09T18:47:12Z**

ready for implementation

**2026-08-10T07:18:05Z**

Coverage note, so the numbers do not confuse you. .coveragerc is now the only coverage config, and its omit list already excluded 'admin.py' and '*/urls.py' before this plan started. So main/admin.py will report no coverage however many tests you add. That is expected; this ticket asks for admin.py to be exercised at changelist level, not for a coverage number on it. Do not change the omit list to chase one. The 'around 70 percent' target applies to main/models.py only.
