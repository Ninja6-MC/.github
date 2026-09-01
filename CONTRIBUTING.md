# Contributing to Ninja6-MC

These are the org-wide defaults. They apply to any [Ninja6-MC](https://github.com/Ninja6-MC)
repository that does not ship its own `CONTRIBUTING.md`; where a repo does ship one, that
file wins outright — it is a fallback, not a merge — and it will carry the build- and
language-specific detail this one cannot.

---

## 1. Code of Conduct

Be respectful and constructive. See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

---

## 2. Branch Naming

`main` is the trunk. Everything else is a short-lived branch that merges back into it
through a pull request; there is no long-running integration branch.

Name branches `<type>/<short-kebab-slug>`, where `<type>` is the same vocabulary as
[Conventional Commits](https://www.conventionalcommits.org/), so the branch and the commits
on it agree:

| Type | Use for | Example |
| :--- | :--- | :--- |
| `feat/` | New functionality | `feat/sqlite-storage` |
| `fix/` | Bug fixes | `fix/authme-double-allocation` |
| `docs/` | Documentation only | `docs/branch-naming-convention` |
| `refactor/` | Restructuring with no behaviour change | `refactor/extract-terrain-scorer` |
| `perf/` | Performance work | `perf/cache-chunk-profiles` |
| `test/` | Tests only | `test/spiral-math-edge-cases` |
| `chore/` | Build, CI, tooling, dependencies | `chore/bump-gradle-9` |

Rules:

* Lowercase, hyphen-separated, no underscores or spaces.
* Describe the change, not the author or the tool that made it — `feat/folia-scheduler`,
  never `bharath/patch-2` or a generated name like `claude/fix-77c354`.
* Keep it short. Two or three words is usually enough; the PR title carries the detail.
* One branch per logical change. If you find yourself naming it `feat/misc`, it should be
  two branches.

Automated agents and bots follow the same scheme. If a tool creates a branch under its own
default name, rename it before opening the PR:

```bash
git branch -m feat/my-actual-change
```

If the old name was already pushed, publish the new one and delete the old, or the stale
branch outlives the rename:

```bash
git push -u origin feat/my-actual-change && git push origin --delete <old-name>
```

---

## 3. Development Workflow

1. **Fork & Clone**, and add the upstream repository so you can keep `main` current:
   ```bash
   git clone https://github.com/<your-username>/<repo>.git
   cd <repo>
   git remote add upstream https://github.com/Ninja6-MC/<repo>.git
   ```
2. **Branch from an up-to-date `main`**:
   ```bash
   git checkout main
   git pull upstream main   # `origin` if you are working in the repository itself
   git checkout -b feat/my-new-feature
   ```
3. **Coding standards.** Plugin repos target Java 21 LTS, follow standard Java naming
   conventions, and must use Paper's async API (`world.getChunkAtAsync(...)`) rather than
   blocking the main thread. Non-plugin repos follow the idiom of whatever they are
   written in. Either way, match the surrounding code.
4. **Tests.** Add tests for any logic or arithmetic you change. Run the repo's own test
   command before opening a PR — for a Gradle repo that is `./gradlew test`.
5. **Commit messages.** Follow [Conventional Commits](https://www.conventionalcommits.org/):
   * `feat(math): add hexagonal plot calculation`
   * `fix(authme): resolve race condition on delayed join`
   * `docs(readme): add bStats configuration instructions`

   **Keep them short.** The subject usually says everything. Add a body only when the
   subject cannot carry it, and keep it to a line or two — reasoning, alternatives
   considered and background belong in the pull request description, where a reviewer
   reads them, not in `git log`. Wrap the body at 72 characters; git never reflows it.
6. **Sign off every commit**:
   ```bash
   git commit -s -m "fix(authme): resolve race condition on delayed join"
   ```
   `-s` appends a `Signed-off-by` line. See [section 5](#5-licensing-of-contributions)
   for what that certifies. CI checks it on every pull request.

---

## 4. Submitting Pull Requests

1. Push your branch to your fork.
2. Open a pull request targeting **`main`**.
3. Complete the PR checklist.
4. Ensure all GitHub Actions checks pass. `main` is protected: CI must be green and the
   branch up to date before it can merge.
5. PRs are squash-merged, so the PR title becomes the commit on `main` — write it as a
   Conventional Commit.

### PR Review & Iteration Workflow
When feedback or review comments are received on an open pull request:
* **No Force-Pushing During Active Review**: Keep existing commits intact and never amend or force-push during an ongoing review cycle so reviewers can inspect the exact delta using GitHub's review diff tools.
* **Separate Fix Commits**: Address review comments in new, standalone commits with DCO sign-offs (`git commit -s`):
  ```bash
  git commit -s -m "fix(compiler): clamp concurrency and add whitelist extension guard"
  git push origin feat/your-branch-name
  ```
* **Link Commits to Comments**: When responding to review comments or resolving threads, cite the specific commit SHA(s) that introduced each fix (e.g., `Resolved in 51de542: ...`).
* **Squashing at Merge**: Linear history is maintained by squashing or rebasing when merging the pull request into `main`.

---

## 5. Licensing of Contributions

Ninja6-MC projects are [GPL-3.0](https://www.gnu.org/licenses/gpl-3.0.en.html) unless the
repository states otherwise, and every contribution is published under that repository's
licence. You keep the copyright in what you write; nothing here assigns it away.

Signing off a commit means two things:

1. You certify the [Developer Certificate of Origin 1.1](https://developercertificate.org/)
   — in short, that you wrote the contribution or otherwise have the right to submit it
   under the project's licence.
2. You grant Ninja6-MC a perpetual, worldwide, non-exclusive, royalty-free and irrevocable
   licence to use, reproduce, modify and distribute your contribution, **including under
   licence terms other than GPL-3.0**.

Point 2 is the part that goes beyond a plain DCO, so it is worth being direct about why it
is here. It keeps a project able to change its licence, or to offer the same code under
separate terms, without having to track down and get agreement from every past contributor,
which is impossible in practice once a project has been around for a while. It does not
take anything away from you: your contribution still ships publicly under GPL-3.0, and you
remain free to use your own work however you like.

Add the sign-off with `-s`:

```bash
git commit -s -m "fix(spawn): reject candidates adjacent to powder snow"
```

which appends a line to the commit message:

```
Signed-off-by: Your Name <your.email@example.com>
```

Use your real name and an email you can be reached at. The DCO check fails a pull request
if any commit is missing the line. To fix the most recent commit:

```bash
git commit --amend -s --no-edit
```

To fix a whole branch, rebase against `main` with sign-off applied to every commit:

```bash
git rebase --signoff origin/main
```

Both rewrite history, so force-push the branch afterwards.
