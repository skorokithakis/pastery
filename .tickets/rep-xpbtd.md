---
id: rep-xpbtd
status: closed
deps: []
links: []
created: 2026-08-10T19:49:55Z
type: chore
priority: 1
assignee: Stavros Korokithakis
---
# Delete the dead ban_ip path in remove_spam

Objective: remove the unreachable Cloudflare IP-banning code and everything that exists only to serve it.

ban_ip in main/management/commands/remove_spam.py cannot run. Its first statement is 'return True'. Delete the function and both 'ban_ip(paste.user_address)' call sites in handle(). Removing them is behaviour-neutral: the calls already did nothing and their return value was discarded.

That orphans three imports in the same file (requests, datetime, django.conf.settings; each is used only by ban_ip) and both CLOUDFLARE_EMAIL and CLOUDFLARE_API_KEY in pastery/settings.py, which nothing else reads. Delete all of those.

Non-goals: do not touch the rest of the spam command. calculate_link_ratio, the regex path, the link-ratio path and the spam-terms path all stay exactly as they are. Do not change what the command deletes.

Context: S1-ixple kept the two Cloudflare settings because ban_ip referenced them. This ticket removes the reference, so they go.

## Acceptance Criteria

Suite green. No hit for ban_ip, CLOUDFLARE_EMAIL or CLOUDFLARE_API_KEY anywhere in the repo.


## Notes

**2026-08-10T19:49:59Z**

ready for implementation
