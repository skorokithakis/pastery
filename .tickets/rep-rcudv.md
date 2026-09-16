---
id: rep-rcudv
status: closed
deps: []
links: []
created: 2026-09-16T19:30:11Z
type: task
priority: 2
assignee: Stavros Korokithakis
---
# Keep site-page pastes out of the noindex rule

Objective: /api/, /about/ and /plugins/ are pastes (they fall through main/urls.py to the ^(?P<paste_id>[^/]+)/$ pattern), and commit 7b915c3 made the paste view noindex them. They are real site pages, linked from base.html and listed in StaticViewSitemap. Google Search Console now reports them as 'Excluded by noindex tag'. Make them indexable again.

Scope:
- pastery/settings.py: add INDEXABLE_PASTE_IDS = {"api", "about", "plugins"}, with a comment saying these pastes serve as site pages and are submitted in the sitemap.
- main/views.py: in the paste view only, skip setting X-Robots-Tag when paste_id is in that set. Note the raw-html branch sets its own response earlier; the header line is shared by both branches, so guard the single line.
- main/tests_smoke.py: add a test that walks StaticViewSitemap.items(), GETs each URL and asserts no X-Robots-Tag on the response. This is the regression guard: anything we submit to Google must be indexable. It needs pastes with ids api, about and plugins to exist in the fixture, otherwise those URLs 404.

Non-goals:
- Do NOT add noindex to /sitemap.xml. Explicitly rejected by the product owner.
- Do NOT add a robots.txt (see .gnosis: Disallow and X-Robots-Tag are mutually exclusive here).
- Do NOT change raw_paste, download_paste or embed_paste. Only the HTML page needs to be indexable.
- Do NOT add a model field or admin toggle. The allowlist is a setting on purpose.
- Do NOT change the sitemap item list or the unanchored 'sitemap.xml' url pattern.

Caveat: paste_id can be a '+'-joined list of ids for combined pastes. A combined id must never match the allowlist; a plain membership test on the raw paste_id string gives that for free.

Ready for implementation.

## Acceptance Criteria

GET /about/, /api/ and /plugins/ return no X-Robots-Tag. An ordinary paste still returns 'noindex, nofollow' on all four paste views. Existing noindex tests still pass. Suite green.

