# Release standards

Normative text for `N6-REL-01`. The register is in [`README.md`](README.md).

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
rather than of a repository, the two existing implementations differ in what they do with
the notes afterwards, and a rule asserting a specific script shape would be asserting more
than has been agreed. Revisit once a third publishing repository exists.

### Versioning is not specified here

Whether a repository is on the `0.MINOR.PATCH` track or `MAJOR.MINOR.PATCH` is its own
decision and belongs in its `RELEASE_PROCESS.md`. What the register requires is that the
choice is **written down**, because the leading digit is a promise about stability and an
undocumented one gets made differently by each person who reads it.

`Keyframe` is pre-1.0 and says so. `SpiralGenesis` is not. Both are correct.
