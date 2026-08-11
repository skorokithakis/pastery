---
id: rep-bjbzt
status: closed
deps: []
links: []
created: 2026-08-11T22:31:23Z
type: bug
priority: 2
assignee: Stavros Korokithakis
external-ref: STA-114
---
# Split the duplicate Markdown dropdown entry into rendered and source

Ready for implementation.

Objective: the language dropdown lists "Markdown" twice, both with value `markdown`. Remove the duplicate, and add a separate "Markdown (source)" choice that syntax-highlights Markdown source instead of rendering it to prose.

Cause: get_languages() in main/models.py drops Pygments own Markdown lexer via `banned_lexers = ["md"]`, which matches only the lexer FIRST alias. Pygments now reports the Markdown aliases as ("markdown", "md"), so the ban misses and the lexer entry survives next to the hand-written one. Both end up as ["markdown", "Markdown"], identical value and label, so the choice a user clicks makes no difference today. `markdown` is the only duplicate value in the 599-entry list.

Scope, main/models.py:
- get_languages(): match banned_lexers on the lexer NAME rather than its first alias, so Pygments Markdown lexer is excluded again and stays excluded when aliases get reordered. Add ["markdown-source", "Markdown (source)"] to the hand-written entries alongside textile and raw html, and add "markdown-source" to the `top` list. The list is sorted by value, so it lands next to `markdown`.
- get_aliases(): add "markdown-source" mapped to itself. This is load-bearing twice over. The `language` property normalises through ALIAS_DICT, and api/views.py:101 validates with ALIAS_DICT.get(x, "autodetect"), so without the entry the API would silently degrade the new value to autodetect.
- rendered_body (~line 679) and filename (~line 624) both hand `language` to get_lexer_by_name. `markdown-source` is not a Pygments alias, so it raises ClassNotFound there. Map it to the real `markdown` lexer at both sites; one small module-level dict is enough.

Constraints and caveats:
- `markdown` and `md` must keep meaning "render as Markdown". Do not repurpose `md` for the source variant; API clients rely on the current meaning.
- The value string `markdown-source` is public API surface. It appears in the HTTP API and in get_language_display(). Use exactly that spelling.
- No template changes needed. paste.html:133, embed.html:17 and views.py:245 test `language == "markdown"` to select the prose CSS class and layout. A distinct value is correctly false for all three, so the source variant gets code styling and the highlight path for free. Verify this holds; do not edit the templates.
- No migration expected. raw_language deliberately carries no choices, see the comment at models.py:505. Confirm makemigrations --check --dry-run stays clean.

Non-goals:
- Do not make autodetect able to pick markdown-source. guess_lexer returns `markdown` for Markdown-like text, so autodetected pastes render as prose. That is intended.
- Do not touch the textile or raw html entries.
- Do not reorder or restyle the dropdown beyond adding the one entry.
- No data migration and no change to any stored raw_language value.

## Design

Rejected: using `md` as the source value. Pygments accepts it directly, so it would avoid the lexer override, but get_aliases() folds every Markdown alias into `markdown`, so `md` would need carving out of the fold, and posting language=md through the API would flip from rendered to highlighted for existing clients.

Rejected: a per-paste "render this" boolean. That means a migration plus a new form and API field, which is more surface than a second language value for the same result.

Chosen: a sentinel value Pygments does not own, so ALIAS_DICT passes it through untouched and the template equality tests fall on the correct side without being edited. The cost is the two get_lexer_by_name call sites, which need the sentinel mapped back to a real lexer.

## Acceptance Criteria

The dropdown shows one "Markdown" and one "Markdown (source)", adjacent. LANGUAGES has no duplicate values and no duplicate labels. A paste with raw_language="markdown-source" reports language "markdown-source", renders as highlighted source rather than prose, gets a filename ending .md, and has a working get_language_display(). The API accepts language=markdown-source without falling back to autodetect. Existing markdown and md behaviour is unchanged, including the golden rendering test in tests_models.py. makemigrations --check --dry-run is clean and the full suite is green.


## Notes

**2026-08-11T22:45:15Z**

Implemented. Duplicate removed by banning Pygments' Markdown lexer on name rather than first alias; new 'markdown-source' / 'Markdown (source)' choice added, mapped to the real markdown lexer at the two get_lexer_by_name sites. Review also found get_aliases() had the same latent alias-order assumption (hand-written entries were seeded before the Pygments loop, so the loop overwrote them); hardened by applying them after the loop and pinning md -> markdown. Verified no-op against the old ALIAS_DICT apart from the new key. 74 tests OK, makemigrations clean. Knowledge recorded in gnosis payxne.
