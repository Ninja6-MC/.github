# `templates/`

Files a new repository still has to **copy**, because GitHub has no inheritance
mechanism for them. Everything in the parent directory is inherited automatically and
must not be copied.

They carry a `.template` suffix rather than their real names on purpose. A real
`.gitattributes` sitting here would apply to this directory, and a real
`.editorconfig` starting with `root = true` would cut off editorconfig resolution
for everything under it. Both are harmless while the directory holds nothing they
match, and stop being harmless the moment someone adds a sample file. **Rename on
copy.**

| File | Copy to | Notes |
|---|---|---|
| `editorconfig.template` | repo root, **renamed to `.editorconfig`** | Unchanged otherwise. 4-space indent, LF, UTF-8; 2 for YAML. |
| `gitattributes.template` | repo root, **renamed to `.gitattributes`** | Drop the `gradlew*` lines in a non-Gradle repo; keep the rest. |
| `dco-stub.yml` | `.github/workflows/dco.yml` | Calls the reusable check. Do not copy the check itself. |
| `standards-stub.yml` | `.github/workflows/standards.yml` | Calls the reusable standards check. Add it when the repo adopts the register, not before. |
| `dependabot.template` | `.github/dependabot.yml`, **renamed** | Keeps SHA-pinned actions current. Grouped, with majors split out. Inert at this path, but suffixed like the other copies so nobody has to check whether it is live config for this repo. |
| `scorecard-stub.yml` | `.github/workflows/scorecard.yml` | Calls the reusable OpenSSF Scorecard run. **Public repos only** — private repos cannot publish results or upload SARIF on the Free plan. |

Not templated, and why:

* **`.gitignore`** — start from the one your build system's tooling generates, then add
  what the repo actually produces. A generic org-wide `.gitignore` would be mostly
  wrong for every repo and silently under-ignore for at least one.
* **`CHANGELOG.md`** — per-repo content by definition. Copy the *format*
  ([Keep a Changelog](https://keepachangelog.com/)) from `SpiralGenesis`, not the file.
* **`RELEASE_PROCESS.md`** — varies with how the repo publishes. `SpiralGenesis`
  releases a jar to Hangar and Modrinth; `brand` releases nothing. There is no shared
  process yet to write down, and inventing one before the second publishing repo exists
  would be guessing.
* **`LICENSE`** — a deliberate per-repo choice, not a default. Plugin repos are GPL-3.0.

## Conventions the stubs demonstrate

Not rules. Nothing in `standards/` assigns these an ID and no check enforces them, so a
repository that ignores them is not in breach. They are written down because the 2026-08-20
hardening pass established them across `SpiralGenesis` and `SessionPulse`, and a new
repository copying only the files above would silently get none of it.

* **Pin actions to a commit SHA, never a tag**, with the version in a trailing comment:
  `uses: actions/checkout@11d5960... # v4.4.0`. A tag can be repointed at new code with no
  diff and no notification. Copy `dependabot.template` in the same breath, or the pin
  rots. Watch for **annotated** tags - the tag ref's object sha is the tag object, not the
  commit, and pinning to it fails. Dereference through `/git/tags/` first.
* **Declare a top-level `permissions:`** in every workflow, as narrow as the workflow
  allows, and let a job widen it where it must. A job's permissions REPLACE the workflow's
  on a normal run; the cap applies only to a reusable workflow *call*, and exceeding it
  there is a silent `startup_failure`.
* **`persist-credentials: false` on every `actions/checkout`** unless a step does an
  authenticated git operation. The default leaves the token in `.git/config` for anything
  later in the job to find, which matters most in a job holding `contents: write`.

Whether these should become `N6-CI-*` rule IDs is open. As conventions they bind nobody.

## Fixing something here

Change it here first, then propagate. The reason this directory exists is that
`SessionPulse@45787bc` had to copy its conventions out of `SpiralGenesis` — a plugin
repo — because nothing said which copy was canonical. If a fix lands in a project repo
first, bring it back here in the same PR, or the next repo copies the old version.
