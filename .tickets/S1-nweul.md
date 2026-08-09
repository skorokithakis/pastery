---
id: S1-nweul
status: open
deps: [S1-bskcx, S1-bldcp]
links: []
created: 2026-08-09T17:56:12Z
type: chore
priority: 1
assignee: Stavros Korokithakis
---
# Bump the rendering libraries: markdown, bleach, textile, pygments

Objective: bring the text rendering stack up to date while Django is still at 2.0, so that rendering risk is isolated from Django risk.

Bump: markdown 2.6 to 3.x, bleach 3.2 to 6.x, textile 2.2 to 4.x, pygments 2.10 to current, plus requests, shortuuid, schema and html5lib.

Known required code changes:

- utils/md_nofollow.py is written against Markdown 2.6 internals (LINK_RE, LinkPattern, ReferencePattern, AutolinkPattern, AutomailPattern, md.inlinePatterns as a dict, and extendMarkdown taking md_globals). Markdown 3.0 replaced all of it. Rewrite it as a Treeprocessor, registered in extendMarkdown(self, md), that walks the tree and sets rel=nofollow on every 'a' element. That is shorter than the five pattern subclasses it replaces. Do not attempt to port the pattern classes one for one.
- main/models.py calls markdown.markdown(self.body, [extensions]). Markdown 3 takes keyword arguments only; this must become extensions=[...].
- bleach 5 removed the styles argument to clean(). Delete allowed_styles and the styles= argument in main/models.py's clean() helper. Do NOT add a CSSSanitizer to replace it: 'style' is not listed in allowed_attributes for any tag, so style attributes are already stripped and the styles argument has never had any effect. This is a no-op, not a loss.
- Pygments will report a different lexer list, so LANGUAGES changes and makemigrations will produce another large choices migration. Generate it and commit it.
- Check that main/models.py's private Pygments API imports still resolve: _iter_lexerclasses, guess_decode, get_filetype_from_buffer.

In your summary, show the before and after of the golden test output and explain each difference, so I can judge whether any of it is a regression rather than just a formatting change.

Non-goals: do not replace bleach with nh3. Do not touch Django.

Caveat: use Poetry 1.4.0 for lock operations.

## Acceptance Criteria

Golden tests updated deliberately, with the diff explained. The rel=nofollow test still passes. Suite green.


## Notes

**2026-08-09T18:40:51Z**

Ordering change: uv replaces Poetry before this ticket runs. Ignore the 'use Poetry 1.4.0' caveat in the description; there is no poetry.lock by then. Use uv for all lock operations.
