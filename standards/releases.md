# Release standards

Normative text for `N6-REL-01`, `N6-REL-03`, `N6-REL-04` and `N6-REL-05`. The register is in
[`README.md`](README.md).

---

## `N6-REL-01` — a repository that can publish a release documents how

A repository whose workflows can publish a release carries both:

* **`RELEASE_PROCESS.md`** in the repository root — versioning rules, channels, the
  procedure, secrets, and where releases go. Start from
  [`templates/release-process.template`](../templates/release-process.template).
* **`CHANGELOG.md`** in the repository root — on
  [Keep a Changelog](https://keepachangelog.com/), adhering to SemVer.

**The trigger is the capability, not the filename.** A repository is covered when any
workflow is triggered by a version tag, or runs a step that creates a GitHub release.
Renaming `release.yml` does not exempt anything, and a repository that has never cut a tag
is still covered the moment it *could*.

A repository that publishes nothing is not covered and does not need either file. It may
carry them anyway — documenting a process before the first release is foresight
rather than a violation.

### Why both files

They answer different questions and neither substitutes for the other.

`RELEASE_PROCESS.md` is for the person cutting the release: what the version number
promises, which tag produces which channel, what has to be true before tagging. Every one
of those is a decision that is otherwise made from memory, differently each time.

`CHANGELOG.md` is for the person receiving it. **Generated release notes are not a
substitute** — GitHub's `generate_release_notes` produces a list of merged pull request
titles, which records what work happened rather than what changed for a user. Keep both:
the changelog section as the body, generated notes appended below it.

### Gate it in the workflow

The rule checks that the files exist. Existence is the floor, and a changelog that stopped
being updated satisfies it while helping nobody.

Every publishing repository should therefore fail its own **stable** release when
`CHANGELOG.md` has no section for the version being cut, while letting **pre-releases**
ship without one. `SpiralGenesis` established this and `Keyframe` mirrors it; the shell is
in both `release.yml` files and in the template.

That gate is deliberately **not** part of `N6-REL-01`. It is a property of a workflow
rather than of a repository, the existing implementations differ in what they do with
the notes afterwards, and a rule asserting a specific script shape would be asserting more
than has been agreed. Release workflows exist in several repositories;
[.github#29](https://github.com/Ninja6-MC/.github/issues/29) tracks whether
this gate should become a rule.

### Versioning is not specified here

Whether a repository is on the `0.MINOR.PATCH` track or `MAJOR.MINOR.PATCH` is its own
decision and belongs in its `RELEASE_PROCESS.md`. What the register requires is that the
choice is **written down**, because the leading digit is a promise about stability and an
undocumented one gets made differently by each person who reads it.

`Keyframe` is pre-1.0 and says so. `SpiralGenesis` is not. Both are correct.

---

## `N6-REL-03` — build once, test, approve and promote the same bytes

This rule applies to every workflow that can publish a public release artifact,
whether the destination is GitHub Releases, a package registry or both. It covers
stable releases and pre-releases. A repository with no release publisher is not
covered; ordinary CI snapshots are governed separately by `N6-CI-09` and are not
release candidates merely because they are downloadable.

### Candidate and evidence

The build stage creates the complete release candidate once, before publication.
It records a candidate manifest containing the source commit SHA, intended tag and
version, release channel, originating workflow run ID and attempt, a unique
candidate identifier, the expected artifact filenames and each file's SHA-256
digest. The manifest also identifies every intended public destination. Keep the
candidate and manifest together in an immutable or access-controlled retention
location for long enough to complete testing, approval and reasonable retries.
Pin the toolchain and inputs needed for a repeatable build, but never substitute
a later rebuild for this candidate during publication.

The verification stage downloads the retained candidate files and manifest. It
checks the complete file list, the digest of every file, the candidate identifier,
source commit, intended version and channel. It inspects each downloaded artifact's
embedded version and expected contents (for example a plugin descriptor inside a
JAR or pack metadata and file inventory inside a ZIP) against the intended release,
and fails on a mismatch before running the repository's relevant artifact tests
on those same downloaded bytes. Source tests during the build remain useful, but
do not prove that the downloadable JAR or ZIP is sound. Record the verification
run and its result against the candidate identifier and digests.
If a test cannot inspect a finished artifact directly, document how it exercises
that artifact's contents and what gap remains for review.

### Approval and publication

All public release publication waits behind a protected `release` environment
with a required maintainer approval, including a GitHub-only release. The
environment gate applies to the job holding publication permissions and secrets.
Publishing credentials other than the job-scoped `GITHUB_TOKEN` must be scoped to
that protected environment, never provided as equivalent repository or
organisation secrets to the candidate or verification jobs. Grant write
permissions to `GITHUB_TOKEN` only in the gated publisher job; candidate and
verification jobs use read permissions and receive no publishing credentials.
Approval is for the particular verified candidate and its declared destinations;
it is not a substitute for the checks below. Do not approve a deployment from
automation. The external-registry gate tracked in
[.github#49](https://github.com/Ninja6-MC/.github/issues/49) also applies to
GitHub-only publication under this rule.

After approval, the publisher downloads the same retained candidate and evidence.
Before each destination is written, it verifies the manifest, all file digests,
the passing artifact-test evidence, the intended tag's commit against the recorded
source commit, and the version and channel derived from that tag against the
manifest. Reject missing, expired or mismatched evidence. A tag moved after
candidate verification must fail rather than retarget the release. The publish
job contains no build, package or artifact-modifying step; it uploads the verified
files as they are. If a destination alters uploaded bytes, verify what consumers
actually receive where its API permits, and document any unavoidable limit.

Pre-release and stable channel rules remain repository-specific. Promotion must
not turn an alpha, beta or release candidate into a stable or latest release by
default. Keep each destination's version, pre-release flag and channel consistent
with `RELEASE_PROCESS.md` and the candidate manifest. CI snapshot naming under
`N6-CI-09` does not override these release-version rules.

### Retry and partial publication

A retry resumes only destinations that are still absent, using the retained
candidate and the same verification evidence. Before treating a destination as
complete, compare its published files and metadata with the manifest. If the
destination cannot expose a digest or equivalent identity, require a documented
reconciliation step rather than assuming a previous upload matches. Never
overwrite uncertain or mismatched public bytes and never rebuild on retry. An
expired candidate, incomplete test record, mismatched tag, or conflicting
published artifact stops the workflow for maintainer reconciliation. The
repository's release process documents retention duration, destination order,
idempotent retry method and how a partial release is reconciled.
A publisher with several destinations, or one that cannot prove absence, also
follows `N6-REL-05` for attestation, preflight and per-destination retry.

### Enforcement

The register marks this rule **reviewed** because a static repository scan cannot
prove runtime byte identity, environment approval, remote registry contents or
retry behavior. Each release workflow must fail closed at runtime on the
manifest, digest, test-evidence, tag and destination checks above. Reviewers
inspect those checks and the protected environment settings; the workflow run
records the evidence. `N6-REL-01`'s file-presence check does not attest to any
part of this promotion sequence. Repositories adopting this rule should record
transitional exceptions until their publication paths satisfy it.

### Rollout

For [SpiralGenesis #180](https://github.com/Ninja6-MC/SpiralGenesis/issues/180),
[SessionPulse #82](https://github.com/Ninja6-MC/SessionPulse/issues/82) and
[Keyframe #242](https://github.com/Ninja6-MC/Keyframe/issues/242), whose release
publishers predate this rule, `N6-REL-03` becomes applicable on
**2026-10-04**. This staged date permits their `transitional` exceptions to land
after the identifier enters the register but before the rule binds those
repositories. By 2026-10-04, each must either complete and verify its full
release path and environment settings, or record a `transitional` `N6-REL-03`
exception in its own `.github/standards-exceptions.yml`; remove that exception
only upon compliance.
The standards checker rejects unregistered exception IDs, so those entries
cannot land before this rule. A new release publisher created after this rule
lands is covered from its first publication. The staged date and an exception
record the temporary gap; neither makes an unverified release safe to publish.
`TextureStudio`, `brand` and `.github` have no release-artifact publisher at this
point and need no `N6-REL-03` exception. `AntiSpeedrun` publishes GitHub Releases
through a gated `release` environment workflow, with Modrinth and Hangar publishing
planned; it is not in the staged list above.

---

## `N6-REL-04` - Modrinth publishing is upload-only

A repository that publishes to Modrinth does not feature or unfeature versions. The
publish uploads the new version and edits nothing that already exists.

### Publish step

The Modrinth publishing step sets both of these `mc-publish` inputs:

```yaml
modrinth-featured: false
modrinth-unfeature-mode: none
```

A repository that publishes through another tool sets that tool's equivalent, so the
publish performs no feature or unfeature call on Modrinth.

### Token scopes

The `MODRINTH_TOKEN` secret holds exactly these scopes and no others:

* Read projects (`PROJECT_READ`)
* Read versions (`VERSION_READ`)
* Create versions (`VERSION_CREATE`)

It never holds Write versions, any delete scope, or anything broader. The repository's
`RELEASE_PROCESS.md` lists the same scopes, so the token can be recreated correctly.

### Why

A publish must not edit existing versions after an upload. A post-upload edit step needs a
broader token, and it can fail after the new version is already live. That leaves a partial
publication that a rerun cannot complete, because the version it would upload now exists.
This happened on the `SpiralGenesis` 1.0.0-beta.2 release: `mc-publish`'s default
unfeature step received a 401 after the upload had succeeded.

Featuring is cosmetic. Least privilege and an upload-only publish win over it. A
maintainer who wants a version featured does that on Modrinth, outside the release
workflow.

### Enforcement

The register marks this rule **reviewed**. The shared `Standards` check inspects file
presence and file contents of fixed shape; whether a workflow publishes to Modrinth, and
through which tool, is not something it detects today, and a scan keyed on one action's
input names would miss any other publisher. A check scoped to that one action would also
say nothing about the token, whose scopes live in Modrinth and not in the repository.
Reviewers check the publish step's inputs and the scopes documented in
`RELEASE_PROCESS.md`.

### Rollout

`SessionPulse` already complies. `SpiralGenesis` is brought into line by its own pull
request. A repository that has not yet done so records a `transitional` `N6-REL-04`
exception in its `.github/standards-exceptions.yml` until it complies.

---

## `N6-REL-05` - destinations are preflighted, attested per run and published independently

This rule applies to every workflow covered by `N6-REL-03` that publishes to more than
one destination, or to any destination whose absence it cannot prove from its API. It
refines the retry part of `N6-REL-03`; it does not replace any of its checks.

### Two workflows

The candidate workflow builds, verifies and retains the candidate under `N6-REL-03`, and
publishes nothing. A separate publisher workflow is started by `workflow_dispatch` on the
release tag and takes, as inputs, the tag, the candidate run ID, the destinations to
publish in this run (a comma-separated list, defaulting to all declared destinations), and
one boolean absence attestation per destination that needs one. Every publisher job runs
only when `github.ref` is that tag and the tag input matches the release tag pattern. The
concurrency group is keyed on `github.ref` rather than on the input, because a
workflow-level group is evaluated when the run is queued, before any step can validate it.

The publisher accepts a candidate run only when it is a successful run of the repository's
own candidate workflow, for this tag and the tag's commit, and it pins the attempt whose
artifacts it uses. Retain candidates for the repository maximum (90 days on GitHub-hosted
artifact storage) so a single destination can still be retried weeks later. Expiry follows
`N6-REL-03`: an expired candidate stops the publisher, nothing is rebuilt for that tag, and a
destination still missing is recorded in `RELEASE_PROCESS.md` as not published for that tag
and reached by the next release instead.

### Absence attestation

Some registries do not return every version the owner can see. A version list may omit
drafts, unlisted or scheduled versions even with an owner token, and a deleted version may
still block its number. An omitted result is not proof of absence. Where a destination
cannot prove absence, the publisher writes to it only when the maintainer has inspected the
owner inventory for this exact version and set that destination's attestation input to
true for this run. A repository may drop the attestation for a destination only by
recording, in `RELEASE_PROCESS.md`, evidence that its authenticated lookup returns every
hidden and deleted state for that registry.

An attestation belongs to one dispatch and one candidate:

* It is never stored in a repository, environment or organisation variable or secret, or
  in any file that outlives the run.
* It is needed only for a destination that is absent. A destination already complete with
  matching bytes and metadata is verified and skipped without one.
* The publisher refuses a true attestation on any run attempt other than the first. The
  check runs immediately before each upload, in every job that uploads, because re-running
  a single job reuses the outputs of the jobs it depends on.
* The publisher refuses a true attestation while another publisher run for the same tag
  is in progress, or when one finished after this run was created, since that run may
  have written a version the attestation did not see. Every workflow able to write release
  versions, recovery workflows included, shares the publisher's concurrency group.

### Preflight before the first public write

A first job needs no approval and no publishing credentials. It verifies the candidate
run, the candidate and its evidence, rejects a missing attestation for any selected
destination that public lookups do not show as complete, and runs every check that needs
no secret, such as project visibility or a dry run of the upload. Its failures appear
before a maintainer is asked to approve.

Each publish job then runs, before writing anything, the credential checks that can be made
without writing for **every destination selected in this dispatch**, not only its own: the
token is present and accepted, the project is readable, and it is ready to receive versions,
plus upload permission wherever the registry exposes it. A failure stops every destination
before the first public write, so publishing to only some destinations is an explicit choice
made in the dispatch inputs, never the side effect of a prerequisite that could have been
checked.

Some prerequisites can only be proven by the upload itself. A token limited to the
`N6-REL-04` scopes cannot show whether it holds create-version permission, since its scopes
are visible only on Modrinth. `RELEASE_PROCESS.md` lists each such prerequisite and the
destination it belongs to. A failure there is a failure of that destination alone: the
others still publish, and that destination is retried by a new dispatch once the
prerequisite is fixed.

### One job per destination

Each destination publishes in its own job. Every publish job, a GitHub-only one included,
uses the protected `release` environment and depends on the same preflight job, so all of
them wait at the gate together and one approval covers the run. A failure while uploading
to one destination, such as a registry outage, does not stop the others. That destination
is retried later by a new dispatch that selects only it, with a fresh attestation when it
is still absent.

### Shared state follows the highest stable version

A step that changes shared state rather than adding a version, such as syncing a project
page or moving the GitHub "latest" release marker, writes only for the tag that owns that
state. The owner is the highest stable version the repository has published, or, while no
stable version exists, the highest pre-release. A project page is read by people deciding
what to install, and most install stable, so a pre-release never replaces a stable
version's page, and a stable hotfix published after a newer pre-release still owns it.
A release never moves shared state back to a lower version.

The step checks ownership again immediately before it writes, not only in the preflight
job. Every such step, for every tag of the repository, runs in one concurrency group that
is not keyed on the tag, so two tags published at the same time cannot both decide they
own the state. A tag that does not own the state skips the step and says so in the run.

### Enforcement

The register marks this rule **reviewed**. Reviewers check the dispatch inputs, the
attempt and concurrency guards beside each upload, the candidate-run provenance check, the
cross-destination credential preflight, the shared-state ownership check and its
concurrency group, and the absence of any persistent attestation.
Tests in the repository cover the refusal paths: a true attestation on a later attempt, a
missing attestation for an absent destination, a candidate run from another tag or
workflow, a concurrent publisher run, and a shared-state write for a tag that does not own
it, a stable hotfix below a newer pre-release included.

### Rollout

`N6-REL-05` becomes applicable on **2027-01-31**. Until a repository's publisher complies,
it records a `transitional` `N6-REL-05` exception in its `.github/standards-exceptions.yml`
that links its implementation issue. A release publisher created after this rule lands is
covered from its first publication. A GitHub-only publisher meets the attestation part
trivially, since GitHub Releases can be checked directly, and needs only the workflow
shape and guards.
