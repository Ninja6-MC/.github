# Release standards

Normative text for `N6-REL-01` and `N6-REL-03`. The register is in
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
carry them anyway — `SessionPulse` documents a process it has not yet used, which is
foresight rather than a violation.

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
than has been agreed. Three repositories currently publish releases;
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
source commit, intended version and channel, then runs the repository's relevant
artifact tests on those downloaded bytes. Source tests during the build remain
useful, but do not prove that the downloadable JAR or ZIP is sound. Record the
verification run and its result against the candidate identifier and digests.
If a test cannot inspect a finished artifact directly, document how it exercises
that artifact's contents and what gap remains for review.

### Approval and publication

All public release publication waits behind a protected `release` environment
with a required maintainer approval, including a GitHub-only release. The
environment gate applies to the job holding publication permissions and secrets.
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

At adoption, `SpiralGenesis`, `SessionPulse` and `Keyframe` have release publishers
that need implementation work. Each must record a `transitional` `N6-REL-03`
exception in its own `.github/standards-exceptions.yml` immediately after this
rule lands, then remove the exception only after its full release path and
protected environment are verified. The standards checker validates exception
IDs against the merged register, so these entries cannot land before the rule.
The exception records the temporary gap; it does not make an unverified release
safe to publish. `AntiSpeedrun`, `TextureStudio`, `brand` and `.github` have no
release-artifact publisher at this point and need no `N6-REL-03` exception.
