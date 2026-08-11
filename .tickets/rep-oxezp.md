---
id: rep-oxezp
status: closed
deps: []
links: []
created: 2026-08-11T23:08:03Z
type: bug
priority: 3
assignee: Stavros Korokithakis
---
# JavaScript is missing from the top of the language dropdown

Ready for implementation.

Objective: JavaScript does not appear in the pinned group at the top of the language dropdown. It is buried in the long alphabetical list below the separator, despite being one of the most common paste languages.

Cause: the `top` list inside get_languages() in main/models.py contains "js". The list it is matched against holds each lexer first alias, and the JavaScript lexer first alias is "javascript", so the entry never matches anything and is silently a no-op. Same family as rep-bjbzt: an assumption about which Pygments alias comes first. "js" is the only entry in `top` that currently matches nothing; every other one resolves.

Scope, main/models.py:
- Change "js" to "javascript" in the `top` list.
- Lift `top` out of get_languages() to a module-level constant so it can be asserted against. Keep the name descriptive, for example TOP_LANGUAGES.

Add a test in main/tests.py next to LanguageListTests: every entry in the top-languages constant must appear as a value in LANGUAGES. That is the guard for the whole class of bug, rather than for this one entry, and it is why the constant is being lifted out.

Constraints:
- Selecting JavaScript already works, and pastes already store "javascript". This is dropdown placement only. Do not touch aliases, ALIAS_DICT, or any rendering path.
- "js" must keep working as an input, both through the API and through the ?lang= parameter. It resolves via ALIAS_DICT, which is untouched.

Non-goals:
- Do not add, remove or reorder any other language in the top group.
- No migration, no template change.

## Acceptance Criteria

JavaScript appears in the pinned top group of the dropdown, alphabetically between Java and JSON. The top-languages constant is module level and a test asserts every entry in it resolves to a real value in LANGUAGES; that test fails if "js" is put back. Posting language=js still yields a paste whose language is "javascript". Full suite green and makemigrations --check --dry-run clean.


## Notes

**2026-08-11T23:10:03Z**

Fixed: 'js' -> 'javascript', list lifted to module-level TOP_LANGUAGES with a test that every entry resolves to a real LANGUAGES value. Verified the test fails if 'js' is restored. JavaScript now sits between Java and JSON in the pinned group.
