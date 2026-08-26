# Ninja6-MC standards

Every Ninja6-MC repository follows these standards. Where a repository cannot, the
deviation is recorded — see [Exceptions](#3-exceptions). An unrecorded deviation is not an
exception, it is a defect.

This directory is a **registry**, not a second rulebook. Most rules already have normative
text in [`CONTRIBUTING.md`](../CONTRIBUTING.md) or [`README.md`](../README.md); the registry
assigns each one a stable identifier and says where its text lives and how it is enforced.
Rules with no existing home get their own file here. Nothing is restated in two places.

---

## 1. Rule identifiers

`N6-<AREA>-<NN>`. Identifiers are permanent: once assigned, a rule is never renumbered and
a retired rule's number is never reused. Exceptions cite these, so stability matters more
than tidiness.

| Area | Covers |
| :--- | :--- |
| `BRANCH` | Trunk, branch naming |
| `COMMIT` | Message format, sign-off, authorship |
| `CI` | Workflows, checks, branch protection |
| `REPO` | Files a repository must or must not carry |
| `CMD` | Command and permission naming (plugin repos) |
| `REL` | Versioning, changelog, releases |

**Enforcement** column:

* **automatic** — a workflow or branch protection blocks the merge. Not negotiable at
  review time.
* **reviewed** — a human checks it during review.
* **documented** — no mechanical check is possible; it is written down so it can be cited.

---

## 2. The register

### Branches

| ID | Rule | Normative text | Enforcement |
| :--- | :--- | :--- | :--- |
| `N6-BRANCH-01` | `main` is the trunk. Changes reach it only through a pull request | [`CONTRIBUTING.md` §2](../CONTRIBUTING.md#2-branch-naming) | automatic¹ |
| `N6-BRANCH-02` | Branches are named `<type>/<kebab-slug>`, type drawn from the Conventional Commits vocabulary | [`CONTRIBUTING.md` §2](../CONTRIBUTING.md#2-branch-naming) | reviewed |
| `N6-BRANCH-03` | Branch names describe the change, never the author or the tool that made it | [`CONTRIBUTING.md` §2](../CONTRIBUTING.md#2-branch-naming) | reviewed |

¹ By branch protection, and only where branch protection is available. See
`N6-CI-05` and the note on private repositories in §4.

### Commits

| ID | Rule | Normative text | Enforcement |
| :--- | :--- | :--- | :--- |
| `N6-COMMIT-01` | Commit subjects follow Conventional Commits | [`CONTRIBUTING.md` §3.5](../CONTRIBUTING.md#3-development-workflow) | reviewed |
| `N6-COMMIT-02` | Every commit carries a `Signed-off-by` line | [`CONTRIBUTING.md` §3.6, §5](../CONTRIBUTING.md#5-licensing-of-contributions) | automatic |
| `N6-COMMIT-03` | Sign-off uses a real name and a reachable email | [`CONTRIBUTING.md` §5](../CONTRIBUTING.md#5-licensing-of-contributions) | automatic² |
| `N6-COMMIT-04` | The PR title is itself a Conventional Commit, because PRs are squash-merged | [`CONTRIBUTING.md` §4.5](../CONTRIBUTING.md#4-submitting-pull-requests) | reviewed |
| `N6-COMMIT-05` | A commit body is optional and short; reasoning goes in the pull request | [`CONTRIBUTING.md` §3.5](../CONTRIBUTING.md#3-development-workflow) | reviewed |

² The DCO check verifies the line is present and well-formed. It cannot verify the name
is real or the address reachable.

### Continuous integration

| ID | Rule | Normative text | Enforcement |
| :--- | :--- | :--- | :--- |
| `N6-CI-01` | Every repository runs the shared DCO check by calling the reusable workflow, not by keeping a local copy | [`ci.md`](ci.md) | automatic³ |
| `N6-CI-02` | Reusable workflow references spell `.github` twice | [`ci.md`](ci.md) | documented |
| `N6-CI-03` | A required status check must name a check that actually reports | [`ci.md`](ci.md) | documented |
| `N6-CI-04` | Workflow YAML is committed with LF endings | [`repo-layout.md`](repo-layout.md) | automatic³ |
| `N6-CI-05` | Public repositories protect `main`: pull request required, CI green, linear history, administrators included | [`ci.md`](ci.md) | reviewed |
| `N6-CI-06` | Every third-party action is referenced by commit SHA, never by tag | [`ci.md`](ci.md) | automatic³ |
| `N6-CI-07` | Every workflow declares an explicit `permissions:` grant rather than running on the repository default | [`ci.md`](ci.md) | automatic³ |
| `N6-CI-08` | A checkout that does not set an explicit `token:` sets `persist-credentials: false` | [`ci.md`](ci.md) | automatic³ |

### Repository contents

| ID | Rule | Normative text | Enforcement |
| :--- | :--- | :--- | :--- |
| `N6-REPO-01` | A repository relies on org-inherited health files unless it genuinely needs its own | [`repo-layout.md`](repo-layout.md) | reviewed |
| `N6-REPO-02` | A repository that defines **any** file in `.github/ISSUE_TEMPLATE/` must also define `config.yml` | [`repo-layout.md`](repo-layout.md) | automatic³ |
| `N6-REPO-03` | `assets/` is delivered by the sync pipeline and is never hand-edited | [`repo-layout.md`](repo-layout.md) | automatic³ |
| `N6-REPO-04` | `.editorconfig` and `.gitattributes` come from [`templates/`](../templates) | [`repo-layout.md`](repo-layout.md) | reviewed |
| `N6-REPO-05` | Every repository carries a `standards-exceptions.yml`, even when it has no exceptions | this file, §3 | automatic³ |

³ Checked by the `Standards` workflow in this repository
([`.github/workflows/standards.yml`](../.github/workflows/standards.yml), logic in
[`scripts/check-standards.py`](../scripts/check-standards.py)), which every adopted
repository except this one calls through a stub — this one hosts it instead — **and
required on every repository whose `main` can be protected**, so a violation blocks the
merge rather than waiting for a reviewer to notice it.

`brand` is the exception, and it is already recorded as one: the check runs and reports
there, but a private repository on the Free plan cannot have branch protection at all, so
nothing can be required. That is its `permanent` `N6-BRANCH-01` entry.

The workflow is exception-aware: a failure whose rule has an entry in the repository's
`standards-exceptions.yml` is reported as a notice and does not fail the run. `N6-REPO-05`
is the exception to that — a malformed exceptions file cannot excuse itself.

---

## 3. Exceptions

Each repository carries **`.github/standards-exceptions.yml`**. The file is required even
when the list is empty (`N6-REPO-05`) — an absent file is indistinguishable from an
oversight, whereas an empty one is a statement.

```yaml
# .github/standards-exceptions.yml
repo: <repo>
exceptions:
  - rule: N6-CI-01
    type: transitional
    reason: >
      Still runs a local copy of the DCO workflow. Adopting the shared stub renames the
      reported check from `Check Sign-off` to `dco / Check Sign-off`, so the swap has to be
      sequenced against this repository's required-status-check list (N6-CI-03) or pull
      requests block on a check name that no longer reports.
    approved_by: bharathasl74185@gmail.com
    approved_on: 2026-08-19
    revisit_by: 2026-11-19
```

Every field is required.

`type` is either **`permanent`** — the repository *cannot* comply, and no amount of work
would change that — or **`transitional`**: it can comply and does not yet. Keeping the two
apart is the point of the field. A permanent exception is a fact about the platform; a
transitional one is a task with a deadline, and the register doubles as the list of them.

`reason` says why. For a permanent exception, why compliance is impossible — not that it
would be inconvenient. For a transitional one, what has to happen first and in what order.

`revisit_by` is a date, never `never`. A permanent exception that keeps being re-approved
is a sign the rule is wrong; change the rule instead of renewing the exception.

An expired `revisit_by` does not fail the build. It is a prompt, and it is the agenda for
the next standards review.

## 4. Where a standard cannot apply

Some rules are impossible rather than inconvenient, and the register says so rather than
pretending otherwise.

**Private repositories cannot have branch protection.** On the **Free plan** GitHub
restricts both branch protection and rulesets to public repositories; the API answers `403
Upgrade to GitHub Pro or make this repository public` for each. On `brand`,
`N6-BRANCH-01` is convention only and cannot be enforced server-side.

That belongs in `brand`'s exceptions file as a `permanent` entry rather than being quietly
ignored — permanent for as long as the organisation stays on Free and the repository stays
private. Changing either would lift it, which is exactly the kind of thing the register
should make visible.

**Private repositories inherit nothing** from this repository — no health files, no issue
templates. `N6-REPO-01` does not apply to them.

## 5. Changing a standard

Open a pull request against this directory. A change that tightens a rule lands together
with the exceptions it creates — as `transitional` entries where the repository will
comply, and `permanent` ones where it cannot — so that no repository is put in breach by a
document it had no chance to answer.

That obligation starts once a repository has adopted the register. It cannot apply to this
first commit, which creates the register itself; see §6.

Adding a rule means saying, in the same pull request, how it will be enforced. A rule with
no enforcement column is an opinion.

## 6. Adoption

This register describes the target state. It was written after the repositories, not
before them, so at the moment it lands most of them do not yet meet it.

A repository is **adopted** when it carries `.github/standards-exceptions.yml`. Until then
it is *not yet adopted* rather than in breach — the distinction matters, because a rule
nobody has had the chance to answer is not a defect anyone committed.

Adoption order, and why:

1. **`.github`** — this repository, with this commit. It hosts the workflow gating every
   other repository's pull requests, so its own `main` being unprotected outranks
   everything else.
2. **`SpiralGenesis`** — the only repository currently receiving contributions.
3. **`brand`** — private, so several rules cannot apply to it at all; its file will be
   mostly `permanent` entries.
4. **`SessionPulse`** — last, in a single pass, once the register has stopped moving.

**Adoption is complete.** All four repositories carry an exceptions file and are measured
by the `Standards` workflow.

The gaps this section originally listed are all closed: `SpiralGenesis` and `SessionPulse`
each kept a local DCO copy (`N6-CI-01`) and shipped issue templates without `config.yml`
(`N6-REPO-02`); `SessionPulse`'s `main` had no required status checks (`N6-CI-05`); and no
repository outside this one carried an exceptions file (`N6-REPO-05`).

One exception remains org-wide, and it is `permanent`: `brand` cannot protect `main` at
all (`N6-BRANCH-01`), because it is private and the organisation is on the Free plan. The
`Standards` check still runs and reports there; it simply cannot block.
