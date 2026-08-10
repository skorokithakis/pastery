---
id: rep-sswqw
status: closed
deps: []
links: []
created: 2026-08-10T19:05:41Z
type: task
priority: 1
assignee: Stavros Korokithakis
---
# Keep raw HTML pastes out of search indexes

Objective: a 'raw html' paste must not pass link equity to a spammer.

main/views.py serves the 'raw html' language verbatim as text/html. The rel=nofollow filter added in rep-dbelk does not apply, because that path never goes through clean(), and it must not: rewriting the body would defeat the feature. The existing Content-Security-Policy on that response sandboxes browsers but means nothing to a crawler.

Add 'X-Robots-Tag: noindex, nofollow' to that response, alongside the CSP header that is already there. Put a short comment saying why: the body is user HTML that is deliberately served unsanitised, so the crawler directive is the only lever available.

Add a test asserting the header is present on a raw html paste.

Non-goals: do not touch any other view. Normal pastes stay indexable, and their links are already nofollowed. The plain-text raw views need nothing. Do not modify the CSP header. Do not sanitise or rewrite the raw HTML body. No dependency or settings changes. Do not bundle S1-ixple or any other modernisation ticket into this.

## Acceptance Criteria

A 'raw html' paste response carries X-Robots-Tag: noindex, nofollow. Covered by a test. No other view changes. Suite green.


## Notes

**2026-08-10T19:05:44Z**

ready for implementation
