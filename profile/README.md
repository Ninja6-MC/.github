<p align="center">
  <img src="../assets/ninja6-primary-256.png" width="128" alt="Ninja6">
</p>

<!-- assets/ is a copy, kept current by the Sync Assets workflow in Ninja6-MC/brand.
     It is a copy rather than a link because `brand` is private and a sibling repo:
     raw.githubusercontent.com 404s for a private repo, and relative paths do not cross
     repository boundaries. See brand/ICON_PLAN.md section 1.

     If the org profile page ever fails to render this relative path, the safe fallback
     is the absolute raw URL of THIS repo, which is public:
     https://raw.githubusercontent.com/Ninja6-MC/.github/main/assets/ninja6-primary-256.png -->

<h1 align="center">Ninja6</h1>

<p align="center">
  <sub>Server-side Minecraft plugins for Paper and Folia.</sub>
</p>

---

## Projects

| Project | What it does | Status |
|---|---|---|
| [**SpiralGenesis**](https://github.com/Ninja6-MC/SpiralGenesis) | Spiral-pattern spawn distribution — every player gets their own plot, allocated asynchronously | Released |
| [**SessionPulse**](https://github.com/Ninja6-MC/SessionPulse) | — | Early scaffolding |

## How we work

Every repo targets Java 21 and Paper's async API, uses
[Conventional Commits](https://www.conventionalcommits.org/), squash-merges through a
protected `main`, and requires a `Signed-off-by` line on every commit. The details are
in [CONTRIBUTING.md](https://github.com/Ninja6-MC/.github/blob/main/CONTRIBUTING.md).

Bug reports and feature requests are welcome on the relevant project's issue tracker.
Security issues go through a private advisory, never a public issue — see
[SECURITY.md](https://github.com/Ninja6-MC/.github/blob/main/SECURITY.md).
