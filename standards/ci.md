# CI standards

Normative text for `N6-CI-01` … `N6-CI-03` and `N6-CI-05` … `N6-CI-08`. `N6-CI-04` lives in
[`repo-layout.md`](repo-layout.md#n6-ci-04--line-endings). The register is in
[`README.md`](README.md).

---

## `N6-CI-01` — call the shared DCO check, do not copy it

Every repository runs the DCO check by calling the reusable workflow in this repository.
The whole file is, with the SHA taken from the canonical stub rather than retyped:

```yaml
name: DCO

on: pull_request

jobs:
  dco:
    uses: Ninja6-MC/.github/.github/workflows/dco.yml@<sha>  # main @ <date>
```

The canonical copy is [`templates/dco-stub.yml`](../templates/dco-stub.yml). Copy it;
do not retype it.

Every repository that calls it now does. `SpiralGenesis` and `SessionPulse` each kept a full local
copy of the script - byte-identical to each other apart from line endings - and both were
swapped for the stub during adoption. The swap is what renames the reported check, which is
why it has to be sequenced against the required list; see `N6-CI-03`.

This repository satisfies the rule by *hosting* the workflow rather than calling it. Its
`dco.yml` carries both `workflow_call` and `pull_request` triggers, so its own pull
requests are checked by the same script every other repository calls. That is
compliance, not an exception.

A local copy of the check is a standards violation even when its contents are correct,
because a fix to the shared workflow does not reach it. If a repository needs different
behaviour, change the shared workflow or record an exception — do not fork it silently.

## `N6-CI-02` — reusable references spell `.github` twice

```
Ninja6-MC/.github/.github/workflows/dco.yml@<sha>
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

### What is required today

Recorded here because `N6-CI-03` is exactly the rule that gets this wrong, and because a
repository that **calls** the reusable workflows needs a **different string for the same
check** from the one that **hosts** them:

| Repository | Required contexts |
| :--- | :--- |
| `SpiralGenesis` | `Build and Test`, `dco / Check Sign-off`, `standards / Check Standards` |
| `.github` | `Check Sign-off`, `Check Standards` |
| `brand` | none possible — private on Free |
| `SessionPulse` | `dco / Check Sign-off`, `standards / Check Standards` |

`.github` reports both names **unprefixed** because it *hosts* the two reusable workflows
rather than calling them, so there is no calling job to prefix with. Every other
repository calls them through a stub and gets `<job-id> / <job-name>`. Copying one
repository's list to the other blocks every pull request on a name that will never report.

Every name above was read off a real run before being required, not predicted.

**`SessionPulse`'s `Committed Icons Match The Master` is deliberately absent**, and the
reason generalises: it is **path-scoped**, so it does not run on a pull request that
touches no artwork. Measured - it reported on the pull request that changed
`docs/assets/`, and did not report on the one that did not. A required check that does not
report blocks the merge, so a conditional check cannot be required unless it is made to
report a skip.

**`strict` and machine-owned branches: rebase, never the button.** With
"branches must be up to date" on, a sync pull request from the asset pipeline goes
`BEHIND` whenever `main` moves after its last run. The obvious remedy - GitHub's
**Update branch** button, or `gh pr update-branch` *without* `--rebase` - creates a merge
commit, which fails twice over: it breaches `required_linear_history`, and it is not
authored by the bot, so the pipeline's foreign-commit guard then treats the branch as
hand-edited and hard-fails that leg with "refusing to force-push over them". Always
`gh pr update-branch --rebase`, which preserves the author address the guard matches on.

**Scorecard is deliberately absent.** It scores a repository rather than a diff, has no
`pull_request` trigger, and therefore reports no check name at all on a pull request.
There is nothing to require.

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

## `N6-CI-06` — third-party actions are pinned to a commit SHA

Every `uses:` referencing an action outside this organisation names a 40-character commit
SHA, with the human-readable version in a trailing comment:

```yaml
uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262 # v4.4.0
```

A tag is a moving pointer. It can be repointed at new code with no diff, no review and no
notification, and the workflow that ran yesterday is not the workflow that runs today. The
pin closes that.

**It also opens the opposite hole**, and the rule is only half a rule without the other
side: a pin goes stale in silence, because nothing tells you the pinned version was
superseded. Every repository that pins therefore carries `.github/dependabot.yml` — see
`templates/dependabot.template`. A repository that pins without it is worse off than one
that never pinned, because it has bought immutability and paid for it with invisibility.

**Check whether the tag is annotated before pinning to it.** On an annotated tag the ref's
`object.sha` is the tag object, not the commit, and pinning to it fails. Dereference
through `/git/tags/{sha}` first. `actions/checkout`'s `v4` is lightweight and was usable
directly; `ossf/scorecard-action` was not.

**The organisation's own reusable workflows are covered too, and are pinned the same
way.** This reverses an earlier exemption, so the reasoning for the reversal is recorded
here rather than in a commit message.

The exemption argued that pinning would defeat the point of maintaining the checks in one
place, and that the workflows are not third-party code. Both are true and neither turned
out to be the deciding question. What decides it is blast radius: `dco.yml` and
`standards.yml` are required status checks on every protected branch in the organisation,
so the file that decides whether a pull request may merge lives in a different repository
and, at `@main`, is whatever that branch holds at the instant the workflow starts. Third
-party-ness was never the risk. Mutability was, and an in-house mutable ref with seven
callers is a larger exposure than an outside action with one.

This organisation has already had the failure. `fix(ci): drop the workflow-level read-all
that broke every caller` reached all callers at once because they all read `main`. Pinned,
a bad commit reaches nobody until a reviewed pull request in each repository moves the pin.

The exemption was also written while the shared workflows were being brought up, when they
changed eight times in two days and pinning genuinely would have been agony. They have
since stabilised: every change after 26 August 2026 has been a grouped Dependabot action
bump. Dependabot's `github-actions` ecosystem covers reusable workflow calls, so a pinned
reference is maintained by machinery every repository already runs — while a `@main`
reference is one it can never propose an update for, because a branch is not a version.

**What this costs**, stated plainly so it is not rediscovered as a surprise: an urgent fix
to a shared workflow no longer reaches every repository in one merge. It reaches them in
one pull request each. Bump by hand when it is urgent rather than waiting for the weekly
run. That is the trade — a gate that fails closed in one repository is recoverable, and a
gate silently changed in all seven is not.

**What the pin does not cover, stated so it is not mistaken for more than it is.**
`dco.yml` carries its script inline, so pinning it makes the DCO gate genuinely immutable.
`standards.yml` does not: it checks out the register and `check-standards.py` from this
repository at run time, preferring `github.job_workflow_ref` and falling back to
`refs/heads/main`. GitHub leaves that variable empty today, so the code that decides
whether a pull request merges is still read from `main` at job start. The resolver is
written correctly and needs no change — once GitHub populates the variable, a pinned caller
reads the register from its own pin, which is the intended behaviour and not a bug to fix.
Until then the pin buys `standards.yml` a fixed *workflow* and a moving *checker*. That is
still worth having, because the workflow is what holds the permissions grant and the
checkout wiring, but it is half of what `dco.yml` gets.

**Enforcement.** `check-standards.py` applies this rule to the organisation's own reusable
workflows as it does to any other reference. It did not always: the skip was removed only
once every repository had been pinned, because removing it earlier would have failed
`Check Standards` on all of them at once — the same org-wide breakage this rule exists to
prevent, and the same ordering trap as renaming a required check before its callers adopt
the new name.

## `N6-CI-07` — every workflow declares its permissions

A workflow that declares no `permissions:` runs on the repository's default grant, which is
broader than any workflow here needs and changes underneath you when an organisation
setting changes. Every workflow declares an explicit grant.

**The grant may sit at workflow level or at job level.** What the rule forbids is neither
— it is running on the default. Both placements are compliant, and which one is correct
depends on the workflow:

* **Workflow level** is the normal choice, and it acts as a cap.
* **Job level, with no top-level block**, is required where a workflow carries a
  `workflow_call` trigger *and* a job needs a broader grant than a workflow-level cap would
  allow. **A workflow-level `permissions:` CAPS the job in a called workflow** rather than
  being replaced by it, which is not how it behaves on a normal run — there, a job's
  `permissions:` replaces the workflow's.

That distinction is not academic. `read-all` at the top of `scorecard.yml`, against a job
wanting `security-events: write`, produced a `startup_failure`: no job, no annotation and
nothing retrievable through the API. `scorecard.yml` therefore carries no top-level block
and declares its grant on the job, and that is compliance rather than an exception.

`dco.yml` and `standards.yml` are also reusable but keep a workflow-level
`contents: read`, because their jobs need nothing beyond it and the cap is worth having.

## `N6-CI-08` — a checkout does not leave the token behind

`actions/checkout` writes the job's token into `.git/config` by default, where every later
step in the job can read it — including a third-party action that has no business with it.
Unless a checkout is going to be used for an authenticated git operation, it sets:

```yaml
with:
  persist-credentials: false
```

**A checkout that sets an explicit `token:` is exempt**, and that is the mechanical test.
Passing a token is the declaration that the checkout exists in order to push. `brand`'s
`sync-assets.yml` is the case: three checkouts, two read-only and credential-free, and one
that takes a minted GitHub App installation token and pushes the sync branch through it.
Turning credentials off on that third one would break the pipeline, so it keeps them, and
a comment beside each says which is which.

It matters most in a job holding `contents: write` and running a third-party action — the
publish path — which is exactly where it was missing when this rule was written.
