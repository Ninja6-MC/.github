# Discord feeds

`Discord Feeds` polls public GitHub metadata every 15 minutes. GitHub schedules may
run late; this is a periodic feed rather than an immediate delivery guarantee.
The workflow runs only in `Ninja6-MC/.github` on `main`. It neither builds source
nor changes release approval gates. No local Docker service is required.

## Routing

| Destination secret | Content |
| :--- | :--- |
| `DISCORD_DEV_BUILDS_WEBHOOK` | Successful main-branch CI snapshots; published prereleases |
| `DISCORD_RELEASES_WEBHOOK` | Published releases whose `prerelease` metadata is false |
| `DISCORD_STAFF_WEBHOOK` | Main CI failure transitions and subsequent recovery |

Sources are explicitly limited to SpiralGenesis, SessionPulse, and AntiSpeedrun.
Each repository must still be public when polled. Pull requests, forks,
merge-queue runs, unrelated workflows, cancelled builds, and drafts are excluded.
Build notifications require the entire `ci.yml` run to succeed and its named
snapshot artifact to exist, contain bytes, and remain unexpired. Links identify
the run/artifact and mention GitHub sign-in and seven-day CI retention.

Release notifications require uploaded nonempty plugin JAR and matching SHA-256
assets. They link to verified GitHub publication, without claiming availability
on other stores. Release IDs plus stage deduplicate publication, including tags that look
stable but are marked prereleases. Promotion of the same release from prerelease
to stable produces one stable announcement. Demotion and repeated promotion do
not repeat a stage already announced or suppressed in the initial baseline.
Reading actual release metadata also works
when publication used `GITHUB_TOKEN` or later store publication failed.

Only the newest completed main CI run changes the current failure/recovery state.
Repeated failed builds do not repeat an already delivered failure alert. Recovery
is announced only after a failure alert was confirmed. Intermediate transitions
between polls can be coalesced into the newest state.

All messages disable mentions. Discussion, support, announcements, and resource
messages remain manually posted. Keyframe and TextureStudio downloads are not
included until suitable artifact pipelines are established.

## Setup

1. Create separate Discord incoming webhooks in the intended development-build,
   release, and private staff channels. Store their URLs as the three repository
   secrets above. Use the canonical `https://discord.com/api/webhooks/...` form;
   never put URLs in logs, state, issues, or committed files.
2. Create `chore/discord-feed-state` with the single file
   `discord-feed-state.json` containing `{"version": 1}`. Use an orphan branch
   to keep runtime state separate from source. State initialization commits and
   subsequent manual edits must carry the maintainer's identity and DCO sign-off.
3. After the source PR is reviewed and merged, dispatch `monitor` once. The first
   run records a UTC starting timestamp and existing public release stages,
   sending nothing from historical runs or releases. Runs created before that
   timestamp remain excluded, even if they finish afterwards. New releases are
   selected by publication timestamp. Existing baselined releases can still
   produce a later stage announcement even when their publication timestamp
   remains unchanged during promotion.
4. Dispatch `preview` to inspect candidates without changing state or sending
   messages. Verify a representative new build/release and member channel access
   before treating setup as complete.

The monitor has `contents: write` only on its own repository. All state requests
target the exact branch and path above, never `main`. Serialized workflow runs
and Contents API SHA comparisons prevent concurrent state overwrites. State
contains only public project/event identifiers, UTC times, delivery status,
Discord message IDs, initial release stages, and confirmed CI health; no message
bodies or credentials.
State is written only when it changes. Deleting/resetting state can permit replay;
preserve it when repairing configuration. Delivery records are not automatically
pruned, so the file should be monitored for growth.

## Delivery and reconciliation

Before sending, the monitor persists a `pending` intent. A successful Discord
response with `wait=true` must provide a message ID before state becomes `sent`.
Definite HTTP client rejections become `retry` with one-hour backoff and are
retried only while the original event is still a valid candidate. Network errors,
server errors, malformed responses, or a crash after saving intent leave
`uncertain` or `pending` state. Those entries never automatically resend.
The workflow fails while any unresolved entry remains; other eligible deliveries
can still proceed. Failure means delivery requires attention, not that GitHub
publication failed.

To reconcile an unresolved entry:

1. Disable the scheduled workflow temporarily so reconciliation cannot race it.
2. Inspect the intended Discord channel, using the event identifier, source link,
   and recorded UTC time to find the message. Never assume absence merely from a
   failed workflow result.
3. If delivered, mark the entry `sent`, record the actual `message_id`, and, for a
   health event, set that project's health to the event's final `healthy` or
   `failed` value. If confirmed undelivered, remove the entry to allow a new
   attempt when the source is still eligible. If obsolete, remove the entry only
   after confirming its source is no longer eligible. Keep all confirmed entries.
4. Commit the state correction on the exact state branch with the maintainer's
   signed-off identity. Dispatch `preview`, re-enable the workflow, then dispatch
   `monitor`. Uncertain entries cannot be resolved by rerunning alone.

## Weekly draft, manually posted

Every Monday at 09:00 UTC, a read-only job prepares a seven-day template-based
draft. Dispatch `digest` to prepare one on demand. Both retain the draft in the
`discord-feed-draft` artifact, retained for seven days. It includes public
successful-build counts, published-release counts, and source links. It does not
summarize arbitrary release bodies or commit text and never posts to Discord.
Staff review and manually post the digest. Scheduled draft preparation cannot
send messages and has no Discord secrets. There is no automatic announcement
or external-news feed.

## Verification

Run `python3 -m unittest discover -s scripts/tests -v`. The suite covers stage
routing, draft/history exclusions, artifact expiry, failure/recovery, trust
filters, mention suppression, duplicate prevention, conservative uncertain
delivery, retry backoff, and exact state-write branch/path/identity constraints.
`Discord Feed Tests` runs the same suite for pull requests and merge groups.
