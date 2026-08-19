# Security Policy

Applies to every [Ninja6-MC](https://github.com/Ninja6-MC) repository that does not
publish its own policy.

## Supported Versions

Only the latest released version of a project receives security fixes. Older versions are
not backported — a fix ships as a new patch release, and the upgrade path is to take it.
Where a repository has a longer support commitment, it says so in its own `SECURITY.md`,
which supersedes this file.

## Reporting a Vulnerability

**Do not open a public issue.** A Minecraft server exploit is live the moment it is
described publicly, and server operators need the patch to exist before the details do.

Report it privately by opening a **Private Security Advisory** on the affected repository:

```
https://github.com/Ninja6-MC/<repository>/security/advisories/new
```

Include:

* the affected version, and the server software and version it was reproduced on
* steps to reproduce, ideally the smallest case that still triggers it
* what an attacker gains — crash, item duplication, permission bypass, data disclosure

If you are unsure which repository is affected, or the issue spans several, open the
advisory on the one you are most confident about and say so in the report.

## What to Expect

* Acknowledgement within 48 hours.
* An assessment of severity and affected versions, shared with you.
* A patched release, coordinated with you on timing where disclosure is a factor.
* Credit in the advisory and the changelog, unless you would rather not be named.

Please give us a reasonable window to ship a fix before disclosing publicly.
