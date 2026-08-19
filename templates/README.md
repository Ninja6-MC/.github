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

## Fixing something here

Change it here first, then propagate. The reason this directory exists is that
`SessionPulse@45787bc` had to copy its conventions out of `SpiralGenesis` — a plugin
repo — because nothing said which copy was canonical. If a fix lands in a project repo
first, bring it back here in the same PR, or the next repo copies the old version.
