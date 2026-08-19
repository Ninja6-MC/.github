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

² The DCO check verifies the line is present and well-formed. It cannot verify the name
is real or the address reachable.

### Continuous integration

| ID | Rule | Normative text | Enforcement |
| :--- | :--- | :--- | :--- |
| `N6-CI-01` | Every repository runs the shared DCO check by calling the reusable workflow, not by keeping a local copy | [`ci.md`](ci.md) | reviewed³ |
| `N6-CI-02` | Reusable workflow references spell `.github` twice | [`ci.md`](ci.md) | documented |
| `N6-CI-03` | A required status check must name a check that actually reports | [`ci.md`](ci.md) | documented |
| `N6-CI-04` | Workflow YAML is committed with LF endings | [`repo-layout.md`](repo-layout.md) | documented |
| `N6-CI-05` | Public repositories protect `main`: pull request required, CI green, linear history, administrators included | [`ci.md`](ci.md) | reviewed |

### Repository contents

| ID | Rule | Normative text | Enforcement |
| :--- | :--- | :--- | :--- |
| `N6-REPO-01` | A repository relies on org-inherited health files unless it genuinely needs its own | [`repo-layout.md`](repo-layout.md) | reviewed |
| `N6-REPO-02` | A repository that defines **any** file in `.github/ISSUE_TEMPLATE/` must also define `config.yml` | [`repo-layout.md`](repo-layout.md) | reviewed³ |
| `N6-REPO-03` | `assets/` is delivered by the sync pipeline and is never hand-edited | [`repo-layout.md`](repo-layout.md) | reviewed³ |
| `N6-REPO-04` | `.editorconfig` and `.gitattributes` come from [`templates/`](../templates) | [`repo-layout.md`](repo-layout.md) | reviewed |
| `N6-REPO-05` | Every repository carries a `standards-exceptions.yml`, even when it has no exceptions | this file, §3 | reviewed³ |

³ Mechanically checkable, but no check exists yet. These become **automatic** when the
standards workflow lands; until then they are enforced at review. The register says what
is true today, not what is planned.

### Commands, releases

`N6-CMD-*` and `N6-REL-*` are **reserved and not yet assigned.** Their source material
exists but is not yet public: command and permission naming currently lives in the private
`brand` repository, and release process lives in each repository's own
`RELEASE_PROCESS.md`. Both are scheduled to be migrated here. Until they are, do not cite
an identifier from either area — there is nothing behind it yet.

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

Known gaps at the time of writing, none of them yet excepted because their repositories are
not yet adopted: `SpiralGenesis` and `SessionPulse` both keep a local DCO copy (`N6-CI-01`)
and ship issue templates without `config.yml` (`N6-REPO-02`); `SessionPulse`'s `main` is
unprotected (`N6-CI-05`); no repository outside this one yet carries an exceptions file
(`N6-REPO-05`).
