---
id: rep-dbelk
status: open
deps: []
links: []
created: 2026-08-10T18:47:13Z
type: task
priority: 2
assignee: Stavros Korokithakis
---
# Apply rel=nofollow to every rendered link, not just markdown-syntax ones

Objective: every <a href> in a rendered paste carries rel=nofollow, whatever produced it.

Today only markdown-syntax links get it, via utils/md_nofollow.py, which patches markdown's inline patterns. A link written as raw HTML in a markdown paste goes straight through untouched, so any paste can hand out follow links. This is a spam-value hole on a public paste site.

Move the nofollow logic to main.models.clean(). That function is the single choke point: both the markdown and the textile paths pass through it, and nothing outside main/models.py calls it. Use bleach.sanitizer.Cleaner with a custom html5lib filter instead of bleach.clean(); extra filters run after the sanitizer, so the rel survives the attribute allowlist.

Then delete utils/md_nofollow.py and drop NofollowExtension from the markdown.markdown() call.

Preserve any rel tokens the paste already has and add nofollow only if absent, rather than overwriting. rel is in the allowed attribute list, so a paste can legitimately carry rel=noopener and must not lose it.

Scope: main/models.py, delete utils/md_nofollow.py, update the golden tests in main/tests_models.py whose expected HTML changes.

Non-goals: no auto-linking of bare URLs (do not reach for bleach.linkify, it rewrites text and would mangle content). Do not touch the Pygments path, which does not go through clean() and emits no links. Do not change the allowed tag, attribute or style lists. No dependency, lock file or Django version changes. Do not bundle any other modernisation ticket into this.

## Design

Chosen over keeping md_nofollow.py and bolting on a second mechanism for raw HTML, because one choke point is simpler than two and it covers textile as a side effect.

It also removes work from the upgrade chain: md_nofollow.py subclasses markdown's inline pattern classes and defines extendMarkdown(self, md, md_globals), both of which break in markdown 3.x. Deleting the file now means S1-nweul has one less thing to port.

The golden tests written in S1-jlmlp will fail on this change. That is correct and expected; they exist to make exactly this kind of output change visible. Re-baseline them deliberately and eyeball the diff.

rendered_body is cached for CACHING_TIME, 24 hours. Pastes already rendered keep their old HTML until the entry expires or the paste is saved. That is self-healing, so do not add a cache purge or a key version for it.

## Acceptance Criteria

A link written as raw HTML in a markdown paste renders with rel=nofollow, covered by a byte-exact golden test. Markdown-syntax links and textile links still carry it. An existing rel value such as noopener survives, with nofollow added alongside. utils/md_nofollow.py no longer exists and nothing references it. Full suite green.


## Notes

**2026-08-10T18:47:34Z**

ready for implementation
