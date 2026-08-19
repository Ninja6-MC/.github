# CI standards

Normative text for `N6-CI-01` … `N6-CI-03` and `N6-CI-05`. `N6-CI-04` lives in
[`repo-layout.md`](repo-layout.md#n6-ci-04--line-endings). The register is in
[`README.md`](README.md).

---

## `N6-CI-01` — call the shared DCO check, do not copy it

Every repository runs the DCO check by calling the reusable workflow in this repository.
The whole file is:

```yaml
name: DCO

on: pull_request

jobs:
  dco:
    uses: Ninja6-MC/.github/.github/workflows/dco.yml@main
```

The canonical copy is [`templates/dco-stub.yml`](../templates/dco-stub.yml). Copy it;
do not retype it.

At the time of writing only `brand` does this. `SpiralGenesis` and `SessionPulse` both keep
a full local copy of the script, byte-identical to each other apart from line endings. Both
are listed as adoption gaps in [`README.md` §6](README.md#6-adoption).

This repository satisfies the rule by *hosting* the workflow rather than calling it. Its
`dco.yml` carries both `workflow_call` and `pull_request` triggers, so its own pull
requests are checked by the same script every other repository calls. That is
compliance, not an exception.

A local copy of the check is a standards violation even when its contents are correct,
because a fix to the shared workflow does not reach it. If a repository needs different
behaviour, change the shared workflow or record an exception — do not fork it silently.

## `N6-CI-02` — reusable references spell `.github` twice

```
Ninja6-MC/.github/.github/workflows/dco.yml@main
          ^^^^^^^ ^^^^^^^
          repo    directory
```

The reference format is `{owner}/{repo}/.github/workflows/{file}@{ref}`. This organisation's
defaults repository is *itself* named `.github`, so the segment appears twice.

Written once, the reference resolves to `workflows/dco.yml`, which is not a valid workflow
location. **The run then fails at startup with zero jobs**, and the error does not obviously
point at the doubled segment as the cause. This has already cost one debugging cycle.

## `N6-CI-03` — a required check must name a check that reports

The required-status-check list is matched against reported check names as plain strings.
Nothing warns when a required name stops being reported; pull requests simply block
forever on a check that will never arrive.

The name changes when the workflow changes shape. Calling a reusable workflow prefixes the
job: a check reported as `Check Sign-off` by a local workflow is reported as
`dco / Check Sign-off` once the stub calls the shared one.

**Therefore: adopt the stub before adding the check to a required list, or change both
together.** Doing it in the wrong order blocks every open pull request on the repository.

Verify what is actually required, and what actually reported, before changing either:

```bash
gh api repos/Ninja6-MC/<repo>/branches/main/protection --jq '.required_status_checks.contexts'
gh pr checks <pr> -R Ninja6-MC/<repo>
```

## `N6-CI-04` — workflow YAML is committed with LF

See [`repo-layout.md`](repo-layout.md#n6-ci-04--line-endings).

## `N6-CI-05` — public repositories protect `main`

Baseline for every public repository:

* a pull request is required — no direct pushes
* required status checks must pass, and the branch must be up to date
* linear history required
* administrators are included; the protection is not a suggestion for the owner
* force-push and deletion disabled

Private repositories cannot do any of this on the Free plan. See
[`README.md` §4](README.md#4-where-a-standard-cannot-apply).

Protection matters most on **this** repository. `.github` holds the reusable workflow that
gates every other repository's pull requests, and the asset-sync GitHub App holds
`contents: write` here. An unprotected `main` here is the widest hole in the organisation,
not the narrowest.
