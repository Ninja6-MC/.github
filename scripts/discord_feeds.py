"""Publish public build/release metadata with durable, conservative delivery state."""

import argparse
import base64
import copy
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

OWNER = "Ninja6-MC"
STATE_REPO = "Ninja6-MC/.github"
STATE_BRANCH = "chore/discord-feed-state"
STATE_PATH = "discord-feed-state.json"
IDENTITY = {"name": "Bharath", "email": "bharathasl74185@gmail.com"}
PROJECTS = {name: f"{name}-SNAPSHOT" for name in (
    "SpiralGenesis", "SessionPulse", "AntiSpeedrun")}
SECRETS = {"dev": "DISCORD_DEV_BUILDS_WEBHOOK",
           "release": "DISCORD_RELEASES_WEBHOOK", "staff": "DISCORD_STAFF_WEBHOOK"}


def instant(value):
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Feed timestamps must include a timezone")
    return parsed


def stamp(value):
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def validate_state(state):
    if set(state) - {"version", "started_at", "deliveries", "health"} or state.get("version") != 1:
        raise ValueError("Unsupported feed state")
    if state.get("started_at"):
        instant(state["started_at"])
    for project, health in state.get("health", {}).items():
        if project not in PROJECTS or health not in ("healthy", "failed"):
            raise ValueError("Invalid health state")
    for key, entry in state.get("deliveries", {}).items():
        if not re.fullmatch(r"(SpiralGenesis|SessionPulse|AntiSpeedrun):"
                           r"(release:[0-9]+|build:[0-9]+|health:[0-9]+:[0-9]+:(healthy|failed))", key):
            raise ValueError("Invalid delivery identity")
        if set(entry) - {"status", "destination", "recorded_at", "retry_after", "message_id"}:
            raise ValueError("Unexpected delivery data")
        if entry.get("status") not in ("pending", "sent", "retry", "uncertain"):
            raise ValueError("Invalid delivery status")
        if entry.get("destination") not in SECRETS:
            raise ValueError("Invalid delivery destination")
        if ":build:" in key and entry["destination"] != "dev":
            raise ValueError("Invalid build destination")
        if ":health:" in key and entry["destination"] != "staff":
            raise ValueError("Invalid health destination")
        instant(entry["recorded_at"])
        if "retry_after" in entry:
            instant(entry["retry_after"])
        if "message_id" in entry and not re.fullmatch(r"[0-9]+", entry["message_id"]):
            raise ValueError("Invalid message identity")
        if entry["status"] == "sent" and "message_id" not in entry:
            raise ValueError("Confirmed delivery needs its Discord message ID")
        if entry["status"] == "retry" and "retry_after" not in entry:
            raise ValueError("Rejected delivery needs backoff")


def already_handled(state, key):
    return state["deliveries"].get(key, {}).get("status") in ("sent", "pending", "uncertain")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


class API:
    def __init__(self, token):
        self.token = token
        self.opener = urllib.request.build_opener(NoRedirect)

    def github(self, path, body=None):
        # Callers use fixed endpoints; redirects must never receive the token.
        if not path.startswith("/repos/Ninja6-MC/"):
            raise ValueError("Unsupported API path")
        if body is not None and (path != f"/repos/{STATE_REPO}/contents/{STATE_PATH}"
                                 or body.get("branch") != STATE_BRANCH):
            raise ValueError("Writes are restricted to the dedicated feed state path and branch")
        request = urllib.request.Request("https://api.github.com" + path,
            data=None if body is None else json.dumps(body).encode(),
            method="GET" if body is None else "PUT", headers={
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "Ninja6-MC-discord-feeds"})
        try:
            with self.opener.open(request, timeout=30) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            raise RuntimeError(f"GitHub API failed with HTTP {error.code}") from None

    def items(self, path, field=None):
        result = []
        separator = "&" if "?" in path else "?"
        for page in range(1, 101):
            data = self.github(f"{path}{separator}per_page=100&page={page}")
            items = data[field] if field else data
            result.extend(items)
            if len(items) < 100:
                return result
        raise RuntimeError("API pagination limit reached; refusing incomplete metadata")

    def discord(self, url, payload):
        if not re.fullmatch(r"https://discord\.com/api/webhooks/[0-9]+/[A-Za-z0-9_-]+", url):
            raise ValueError("Invalid Discord webhook secret")
        request = urllib.request.Request(url + "?wait=true", method="POST",
            data=json.dumps(payload).encode(), headers={
                "Content-Type": "application/json", "User-Agent": "Ninja6-MC-discord-feeds"})
        try:
            with self.opener.open(request, timeout=30) as response:
                message = json.load(response)
                if not re.fullmatch(r"[0-9]+", str(message.get("id", ""))):
                    return "uncertain", None
                return "sent", str(message["id"])
        except urllib.error.HTTPError as error:
            # A definite client rejection did not deliver. Server errors may have.
            return ("retry" if 400 <= error.code < 500 else "uncertain"), None
        except (OSError, ValueError):
            return "uncertain", None


class StateStore:
    def __init__(self, api):
        self.api = api
        self.path = f"/repos/{STATE_REPO}/contents/{STATE_PATH}"
        item = api.github(self.path + "?ref=" + urllib.parse.quote(STATE_BRANCH, safe=""))
        self.sha = item["sha"]
        self.state = json.loads(base64.b64decode(item["content"]))
        validate_state(self.state)
        self.saved = copy.deepcopy(self.state)

    def save(self):
        if self.state == self.saved:
            return
        validate_state(self.state)
        encoded = base64.b64encode(json.dumps(self.state, sort_keys=True).encode()).decode()
        body = {"branch": STATE_BRANCH, "sha": self.sha, "content": encoded,
                "message": "chore(feeds): record delivery state\n\n"
                           "Signed-off-by: Bharath <bharathasl74185@gmail.com>",
                "author": IDENTITY, "committer": IDENTITY}
        result = self.api.github(self.path, body)
        self.sha = result["content"]["sha"]
        self.saved = copy.deepcopy(self.state)


def public_metadata(api):
    projects = {}
    for name in PROJECTS:
        prefix = f"/repos/{OWNER}/{name}"
        repo = api.github(prefix)
        if repo.get("private") is not False or repo.get("full_name") != f"{OWNER}/{name}":
            raise ValueError("Feed source is not the expected public repository")
        runs = api.items(prefix + "/actions/workflows/ci.yml/runs?branch=main&event=push&status=completed",
                         "workflow_runs")
        trusted = [run for run in runs if
                   run.get("event") == "push" and run.get("head_branch") == "main"
                   and run.get("status") == "completed"
                   and run.get("head_repository", {}).get("full_name") == f"{OWNER}/{name}"
                   and run.get("path", "").split("@")[0] == ".github/workflows/ci.yml"]
        releases = api.items(prefix + "/releases")
        projects[name] = {"runs": trusted, "releases": releases}
    return projects


def payload(title, text, url):
    return {"allowed_mentions": {"parse": []}, "embeds": [
        {"title": title[:256], "description": text[:4096], "url": url}]}


def candidates(api, metadata, state, now):
    output = []
    cutoff = instant(state["started_at"])
    for name, project in metadata.items():
        root = f"https://github.com/{OWNER}/{name}"
        for release in project["releases"]:
            if release.get("draft") or not release.get("published_at"):
                continue
            if instant(release["published_at"]) <= cutoff:
                continue
            key = f"{name}:release:{int(release['id'])}"
            if already_handled(state, key):
                continue
            # Announce only a public release with uploaded plugin and checksum assets.
            assets = [a for a in release.get("assets", []) if
                      a.get("state") == "uploaded" and a.get("size", 0) > 0]
            names = {a["name"] for a in assets}
            if not any(n.endswith(".jar") and n + ".sha256" in names for n in names):
                continue
            if not isinstance(release.get("prerelease"), bool):
                raise ValueError("Missing release stage metadata")
            stage = "Prerelease" if release["prerelease"] else "Release"
            tag = str(release["tag_name"])
            link = root + "/releases/tag/" + urllib.parse.quote(tag, safe="")
            output.append((key, "dev" if release.get("prerelease") else "release",
                payload(f"{name}: {stage}", f"Verified GitHub downloads and release notes: {link}", link)))
        for run in project["runs"]:
            if instant(run["created_at"]) <= cutoff or run.get("conclusion") != "success":
                continue
            key = f"{name}:build:{int(run['id'])}"
            if already_handled(state, key):
                continue
            artifacts = api.items(f"/repos/{OWNER}/{name}/actions/runs/{int(run['id'])}/artifacts",
                                  "artifacts")
            artifacts = [a for a in artifacts if a["name"] == PROJECTS[name]
                         and not a.get("expired") and a.get("size_in_bytes", 0) > 0
                         and instant(a["expires_at"]) > now]
            if not artifacts:
                continue
            artifact = artifacts[0]
            link = root + f"/actions/runs/{int(run['id'])}"
            download = link + f"/artifacts/{int(artifact['id'])}"
            text = (f"Experimental main-branch snapshot · commit {str(run['head_sha'])[:7]}\n"
                    f"Download: {download}\nExpires: {artifact['expires_at']} "
                    "(CI retention: 7 days). GitHub sign-in required.")
            output.append((key, "dev", payload(f"{name}: Development build", text, link)))
        # Only the newest main build can change the current health; reruns are considered.
        if project["runs"]:
            latest = max(project["runs"], key=lambda r: (r["run_number"], r.get("run_attempt", 1)))
            conclusion = latest.get("conclusion")
            if instant(latest["created_at"]) <= cutoff or conclusion not in ("success", "failure", "timed_out"):
                continue
            health = "healthy" if conclusion == "success" else "failed"
            previous = state["health"].get(name, "healthy")
            if health != previous:
                key = f"{name}:health:{int(latest['id'])}:{int(latest.get('run_attempt', 1))}:{health}"
                if not already_handled(state, key):
                    link = root + f"/actions/runs/{int(latest['id'])}"
                    title = "Build recovered" if health == "healthy" else "Main build failed"
                    output.append((key, "staff", payload(f"{name}: {title}",
                        "Main-branch CI status changed. Inspect the workflow for details.", link)))
    return output


def deliver(api, store, events, now, webhooks):
    problems = []
    state = store.state
    for key, destination, message in events:
        entry = state["deliveries"].get(key)
        if entry and entry["status"] in ("sent", "uncertain", "pending"):
            continue
        if entry and instant(entry["retry_after"]) > now:
            continue
        # Keep only identifiers/status in the public state, never payloads or secrets.
        state["deliveries"][key] = {"status": "pending", "destination": destination,
                                     "recorded_at": stamp(now)}
        store.save()  # A crash after this point requires manual reconciliation.
        status, message_id = api.discord(webhooks[destination], message)
        entry = state["deliveries"][key]
        entry["status"] = status
        if message_id:
            entry["message_id"] = message_id
        if status == "retry":
            entry["retry_after"] = stamp(now + timedelta(hours=1))
        if status != "sent":
            problems.append(key)
        if ":health:" in key and status == "sent":
            state["health"][key.split(":")[0]] = key.rsplit(":", 1)[1]
        store.save()
    unresolved = [key for key, entry in state["deliveries"].items()
                  if entry["status"] in ("pending", "uncertain", "retry")]
    if unresolved or problems:
        raise RuntimeError("Unresolved feed deliveries; inspect state and reconcile before retrying")


def digest(metadata, now):
    lines = ["# Weekly development digest — draft", "", "Review before posting.", ""]
    cutoff = now - timedelta(days=7)
    for name, project in metadata.items():
        root = f"https://github.com/{OWNER}/{name}"
        successes = [r for r in project["runs"] if r.get("conclusion") == "success"
                     and instant(r["created_at"]) >= cutoff]
        releases = [r for r in project["releases"] if not r.get("draft") and r.get("published_at")
                    and instant(r["published_at"]) >= cutoff]
        lines.extend([f"## {name}", "", f"Successful main builds this week: {len(successes)}.",
                      f"Published GitHub releases this week: {len(releases)}.",
                      f"[Build history]({root}/actions/workflows/ci.yml) · [Releases]({root}/releases)", ""])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("monitor", "preview", "digest"), default="preview")
    parser.add_argument("--output", default="discord-feed-preview.json")
    args = parser.parse_args()
    api = API(os.environ["GH_TOKEN"])
    now = datetime.now(timezone.utc)
    metadata = public_metadata(api)
    if args.mode == "digest":
        Path(args.output).write_text(digest(metadata, now), encoding="utf-8")
        return
    store = StateStore(api)
    state = store.state
    if not state.get("started_at"):
        state.update(started_at=stamp(now), deliveries={}, health={})
        # Baseline is intentionally silent. Future polls announce only newer events.
        if args.mode == "monitor":
            store.save()
        print("Feed baseline initialized; no historical notifications.")
        return
    events = candidates(api, metadata, state, now)
    if args.mode == "preview":
        Path(args.output).write_text(json.dumps(events, indent=2), encoding="utf-8")
        print(f"Prepared {len(events)} delivery candidates; no state or Discord writes.")
        return
    webhooks = {destination: os.environ[secret] for destination, secret in SECRETS.items()}
    for url in webhooks.values():
        if not re.fullmatch(r"https://discord\.com/api/webhooks/[0-9]+/[A-Za-z0-9_-]+", url):
            raise ValueError("Invalid Discord webhook secret")
    deliver(api, store, events, now, webhooks)
    print(f"Processed {len(events)} delivery candidates.")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # Neither urllib exceptions nor response bodies may expose credential URLs.
        print("Feed operation failed. Check configuration and delivery state; secrets withheld.", file=sys.stderr)
        sys.exit(1)
