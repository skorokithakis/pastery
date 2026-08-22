---
id: rep-dhooq
status: closed
deps: []
links: []
created: 2026-08-22T08:45:30Z
type: feature
priority: 2
assignee: Stavros Korokithakis
---
# Keep paste pages out of search indexes

Ready for implementation.

Objective: every response that serves paste content carries 'X-Robots-Tag: noindex, nofollow', so a paste page cannot be indexed by a crawler. This removes the SEO value of link-spam pastes.

Scope: main/views.py, plus tests. Set the header on the four views that serve paste content:
- paste (/<id>/)
- raw_paste (/<id>/raw/)
- download_paste (/<id>/dl/)
- embed_paste (/<id>/embed/)

The 'raw html' branch of paste() already sets this exact header, with a comment explaining why. Leave that line and its comment alone; the new general case makes it redundant but removing it is a separate judgement call. Actually, prefer to fold it into the general path if that reads cleanly, and keep the substance of its comment.

Non-goals:
- Do NOT add a robots.txt or any Disallow rule. Disallow blocks crawling, not indexing, and it would stop the crawler from ever seeing this header. This is deliberate.
- Do NOT touch the home page, the account/login pages, or the static-page sitemap. Those stay indexable.
- Do NOT add the header to the JSON API views or /oembed/.
- Do NOT add a middleware. Four explicit call sites are clearer than an indirect rule.
- Do not touch main/management/commands/remove_spam.py. The spam detector is a separate ticket.

Caveats:
- paste() returns render(...) directly; it needs a local variable to set the header on.
- embed_paste() already builds a response object, and is decorated with xframe_options_exempt.
- download_paste() and raw_paste() return text/plain HttpResponses. A meta tag is impossible there, which is why this must be a header.

## Acceptance Criteria

A test asserts X-Robots-Tag == 'noindex, nofollow' on the response from each of the four paste views. No robots.txt is added. Existing raw-html noindex test still passes. Suite green.

