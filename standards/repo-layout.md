# Repository layout standards

Normative text for `N6-REPO-01` … `N6-REPO-05` and `N6-CI-04`. The register is in
[`README.md`](README.md).

---

## `N6-REPO-01` — inherit health files unless you genuinely need your own

`CONTRIBUTING.md`, `SECURITY.md` and `CODE_OF_CONDUCT.md` are inherited from this
repository **per file**: a repository that defines its own `CONTRIBUTING.md` still
inherits `SECURITY.md`. See [`../README.md` §1](../README.md#1-files-that-are-inherited).

`LICENSE` is **not** in this set. GitHub does not inherit it, and
[`templates/README.md`](../templates/README.md) records it as a deliberate per-repo
choice. Every repository states its own licence.

Define a local copy only when the repository needs to say something different. A local copy
that merely duplicates the org text is a maintenance liability — the org copy will be
updated and the duplicate will not.

## `N6-REPO-02` — defining any issue template means defining `config.yml`

Issue templates inherit **per directory**, not per file. A repository that defines *any*
file in `.github/ISSUE_TEMPLATE/` inherits **none** of the org set — `config.yml` included.

The consequence is not obvious and is not reported anywhere: without an inherited or local
`config.yml`, blank issues stay enabled and the security contact link disappears from the
issue chooser. The repository looks fine; only the chooser is wrong.

There is no way to supply `config.yml` from this repository to one that defines its own
templates. It must be added to that repository:

```yaml
# .github/ISSUE_TEMPLATE/config.yml
blank_issues_enabled: false
contact_links:
  - name: Security vulnerability
    url: https://github.com/Ninja6-MC/.github/security/policy
    about: Report privately. Do not open a public issue.
```

## `N6-REPO-03` — `assets/` is machine-managed

`assets/` in a consuming repository is delivered by the sync pipeline in `brand`, which
opens a pull request whenever `export/` changes. It is not a directory anyone edits.

A hand edit is not rejected — it survives until the next sync and is then silently
overwritten. To change what arrives, change `brand/export/`, or change `dest` for that
consumer in `brand/.github/sync-assets.json`.

Onboarding a consumer takes **two** steps, and the second leaves no trace in git:

1. add the entry to `sync-assets.json`
2. install the `ninja6-asset-sync` GitHub App on the repository, through the organisation
   settings UI

Skipping step 2 fails only that repository's matrix leg. `fail-fast` is off, so the other
legs still succeed — the failure shows as one red leg among green ones rather than an
obviously broken run. At three consumers you notice; at eight you may not.

A repository's own artwork — a plugin icon, a screenshot — is not an org asset and does not
belong in `assets/`. Keep it somewhere the pipeline does not write, such as `docs/assets/`,
and put a README beside it saying which is which.

## `N6-REPO-04` — `.editorconfig` and `.gitattributes` come from `templates/`

Canonical copies: [`templates/editorconfig.template`](../templates/editorconfig.template)
and [`templates/gitattributes.template`](../templates/gitattributes.template). These files
cannot be inherited — GitHub has no mechanism for it — so they are copied, and
[`templates/README.md`](../templates/README.md) records which copy is canonical.

Copying means they drift. When you change one, change the template, and say in the pull
request which repositories still need it.

## `N6-CI-04` — line endings

Git for Windows defaults to `core.autocrlf=true`. Without a `.gitattributes` pinning them,
a clone rewrites line endings on checkout, which:

* breaks shell scripts — the shebang reads as `#!/bin/sh\r` and bash reports
  `bad interpreter: No such file or directory`
* shows files as modified on an otherwise clean checkout — but only where CRLF has
  already been committed, or where git misdetects a binary as text. With LF in the
  repository and `autocrlf=true`, git converts back on commit and the tree stays clean;
  that is the setting working as intended. Marking binaries `binary` is what prevents the
  misdetection case, and stops git corrupting a PNG by "fixing" its endings

At minimum, pin to `eol=lf` every extension the repository actually contains from
`*.sh`, `*.yml`, `*.yaml`, `*.md`, `*.svg` and `*.mjs`; pin Windows batch files to
`eol=crlf`; and mark `*.png`, `*.jar` and `*.zip` as `binary`.

[`templates/gitattributes.template`](../templates/gitattributes.template) is the canonical
starting point and satisfies this. It is Gradle-flavoured — it pins `gradlew` and
`gradlew.bat` — so a non-plugin repository takes the relevant lines rather than the whole
file. This repository's own `.gitattributes` is the non-plugin example.

## `N6-REPO-05` — every repository carries `standards-exceptions.yml`

Normative text is [`README.md` §3](README.md#3-exceptions), which carries the schema, the
worked example, and the `permanent` / `transitional` distinction. It is listed here only so
that this file's account of a repository's required contents is complete.
