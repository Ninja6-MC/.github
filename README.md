# `.github`

Org-wide defaults for [Ninja6-MC](https://github.com/Ninja6-MC). This repository is
not a project — it is the place a shared file lives so it does not have to be copied
into every repo.

GitHub gives a repository literally named `.github` two powers. This repo uses both,
and the distinction matters, because only the first is automatic:

## 1. Files that are inherited

A **public** repo in the org that does **not** define its own copy falls back to the
one here. Nothing is configured; the fallback is the mechanism.

| File | Inherited by |
|---|---|
| `CONTRIBUTING.md` | any repo without its own |
| `SECURITY.md` | any repo without its own |
| `CODE_OF_CONDUCT.md` | any repo without its own |
| `.github/ISSUE_TEMPLATE/*` | any repo without its own |
| `.github/PULL_REQUEST_TEMPLATE.md` | any repo without its own |
| `profile/README.md` | nothing — it *is* the org profile page |

Two limits worth knowing before relying on this:

* **Public repos only.** A private repo inherits nothing from a public `.github`.
* **A local file always wins, per file.** It is not a merge. `SpiralGenesis` defines
  its own `CONTRIBUTING.md` (Gradle, Java 21, `./gradlew test`) and keeps it; it still
  inherits `CODE_OF_CONDUCT.md`, which it does not define.

So the defaults here mostly benefit the *next* repo. That is the point of writing them
before there is a next repo.

## 2. Workflows that are called

`.github/workflows/dco.yml` is a **reusable workflow**. Other repos call it rather
than copying it:

```yaml
# .github/workflows/dco.yml in any Ninja6-MC repo
name: DCO
on: pull_request

jobs:
  dco:
    uses: Ninja6-MC/.github/workflows/dco.yml@main
```

That three-line stub replaces ~60 lines of duplicated shell, and a fix to the check
reaches every repo at once.

**Only genuinely identical jobs belong here.** The icon drift gates in `brand` and
`SpiralGenesis` look like candidates and are not: they run different scripts against
different paths, and `brand/ICON_PLAN.md` §6 argues deliberately for keeping the two
export toolchains separate. Sharing them would couple two things that were split on
purpose.

## 3. Files that arrive by pull request — `assets/`

`assets/` is **machine-managed. Do not edit it here.** The marks in it are copies,
generated from `src/ninja6-master.svg` in [`brand`](https://github.com/Ninja6-MC/brand)
and delivered by that repo's `Sync Assets` workflow as a pull request whenever the
artwork changes. An edit made here survives until the next sync and is then silently
overwritten — fix the master instead.

They are copies rather than links for a reason that is not laziness: `brand` is private,
so `raw.githubusercontent.com` returns 404 for it, and relative paths do not cross
repository boundaries on GitHub. A copy is the only form that renders in a public README,
in a local clone, and on Modrinth and Hangar alike. `brand/ICON_PLAN.md` §1 records the
full argument, including why the obvious objection to copying — that copies drift —
stops applying once a pipeline re-syncs them.

To receive the bundle, a repo adds itself to `.github/sync-assets.json` in `brand` **and**
has the `ninja6-asset-sync` GitHub App installed on it. Both are required; the App install
lives in org settings and leaves no trace in any repository, which is exactly why it gets
forgotten.

## 4. Files that cannot be inherited — `templates/`

GitHub has no fallback for repo-level config. These still have to be copied into a
new repo by hand:

| File | Why it cannot be inherited |
|---|---|
| `templates/.editorconfig` | read by editors from the working tree |
| `templates/.gitattributes` | read by git from the working tree |
| `.gitignore` | too project-specific to template — start from the build system's |
| `CHANGELOG.md` | per-repo content by definition |
| `RELEASE_PROCESS.md` | varies with how the repo publishes |

`templates/` exists to answer one question: **which copy is canonical?** Before this
repo, the answer was "whichever repo you happened to open" — `SessionPulse@45787bc`
copied its conventions out of `SpiralGenesis`, a plugin repo, because there was
nowhere else to copy from. Copy from `templates/` instead, and send fixes back here.

## Related

Org conventions that are prose rather than defaults currently live in
[`brand`](https://github.com/Ninja6-MC/brand): `ICON_PLAN.md` (the icon rulebook, which
stays with the assets it specifies) and `COMMAND_NAMING.md` (command and permission
naming, which has nothing to do with brand and would sit more honestly here — an open
question, not an oversight).

## License

[CC0 1.0 Universal](LICENSE) — public domain dedication. These are templates meant to be
copied; requiring attribution on boilerplate would be friction with no upside. Plugin
repos are GPL-3.0 and unaffected.

Two exceptions, because a blanket dedication cannot cover work that is not ours:

* **`CODE_OF_CONDUCT.md`** is adapted from the [Contributor Covenant](https://www.contributor-covenant.org)
  v2.1, licensed **CC BY 4.0**. The attribution section at the foot of that file is a
  licence condition — keep it if you copy the file.
* **`assets/`** holds Ninja6 marks, synced from `brand`. They are project identity, not
  boilerplate: all rights reserved, and not covered by the dedication above.
