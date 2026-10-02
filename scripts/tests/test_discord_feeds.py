import base64
import copy
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch
import urllib.error

SCRIPT = Path(__file__).parents[1] / "discord_feeds.py"
spec = importlib.util.spec_from_file_location("feeds", SCRIPT)
feeds = importlib.util.module_from_spec(spec)
spec.loader.exec_module(feeds)
NOW = datetime(2026, 10, 2, 12, tzinfo=timezone.utc)


def state():
    return {"version": 1, "started_at": "2026-10-01T00:00:00Z", "deliveries": {}, "health": {}}


def run(**overrides):
    item = {"id": 21, "run_number": 2, "run_attempt": 1, "created_at": "2026-10-02T00:00:00Z",
            "head_sha": "abcdef0123456", "conclusion": "success", "status": "completed",
            "event": "push", "head_branch": "main", "path": ".github/workflows/ci.yml",
            "head_repository": {"full_name": "Ninja6-MC/SpiralGenesis"}}
    return dict(item, **overrides)


def release(**overrides):
    item = {"id": 30, "tag_name": "v0.1.0", "draft": False, "prerelease": True,
            "published_at": "2026-10-02T00:00:00Z", "assets": [
                {"name": "plugin.jar", "state": "uploaded", "size": 10},
                {"name": "plugin.jar.sha256", "state": "uploaded", "size": 64}]}
    return dict(item, **overrides)


class FakeAPI:
    def __init__(self):
        self.outcome = ("sent", "123")
        self.calls = []
        self.artifact = {"id": 42, "name": "SpiralGenesis-SNAPSHOT", "expired": False,
                         "size_in_bytes": 100, "expires_at": "2026-10-09T00:00:00Z"}

    def items(self, path, field=None):
        return [self.artifact]

    def discord(self, url, message):
        self.calls.append((url, message))
        return self.outcome


class Store:
    def __init__(self):
        self.state = state()
        self.saved = []

    def save(self):
        feeds.validate_state(self.state)
        self.saved.append(copy.deepcopy(self.state))


class RoutingTests(unittest.TestCase):
    def candidates(self, runs=None, releases=None, current=None, api=None):
        return feeds.candidates(api or FakeAPI(), {"SpiralGenesis": {
            "runs": runs or [], "releases": releases or []}}, current or state(), NOW)

    def test_prerelease_metadata_overrides_stable_looking_tag(self):
        result = self.candidates(releases=[release()])
        self.assertEqual(result[0][1], "dev")
        self.assertEqual(self.candidates(releases=[release(prerelease=False)])[0][1], "release")

    def test_drafts_incomplete_assets_and_history_are_silent(self):
        self.assertEqual(self.candidates(releases=[release(draft=True)]), [])
        self.assertEqual(self.candidates(releases=[release(assets=[])]), [])
        self.assertEqual(self.candidates(releases=[release(published_at="2026-09-01T00:00:00Z")]), [])

    def test_snapshot_requires_full_ci_success_and_downloadable_artifact(self):
        result = self.candidates(runs=[run()])
        self.assertEqual(len(result), 1)
        self.assertIn("GitHub sign-in required", result[0][2]["embeds"][0]["description"])
        self.assertIn("7 days", result[0][2]["embeds"][0]["description"])
        api = FakeAPI()
        api.artifact["expired"] = True
        self.assertEqual(self.candidates(runs=[run()], api=api), [])
        api.artifact["expired"] = False
        api.artifact["expires_at"] = "2026-10-02T00:00:00Z"
        self.assertEqual(self.candidates(runs=[run()], api=api), [])

    def test_failure_recovery_and_cancellation(self):
        failure = self.candidates(runs=[run(conclusion="failure")])
        self.assertEqual(failure[0][1], "staff")
        self.assertEqual(self.candidates(runs=[run(conclusion="cancelled")]), [])
        current = state()
        current["health"]["SpiralGenesis"] = "failed"
        recovered = self.candidates(runs=[run()], current=current)
        self.assertEqual(recovered[-1][1], "staff")
        self.assertTrue(recovered[-1][0].endswith("healthy"))

    def test_every_payload_suppresses_mentions_and_uses_fixed_github_links(self):
        for _, _, message in self.candidates(runs=[run()], releases=[release(tag_name="@everyone")]):
            self.assertEqual(message["allowed_mentions"], {"parse": []})
            self.assertTrue(message["embeds"][0]["url"].startswith("https://github.com/Ninja6-MC/"))

    def test_delivery_ids_survive_reruns_and_retries_remain_candidates(self):
        current = state()
        current["deliveries"]["SpiralGenesis:release:30"] = {
            "status": "sent", "destination": "dev", "recorded_at": "2026-10-02T00:00:00Z"}
        self.assertEqual(self.candidates(releases=[release()], current=current), [])
        current["deliveries"]["SpiralGenesis:release:30"]["status"] = "retry"
        self.assertEqual(len(self.candidates(releases=[release()], current=current)), 1)

    def test_api_filter_rejects_pr_fork_and_unrelated_workflow(self):
        api = FakeAPI()
        api.github = lambda path: {"private": False, "full_name": path.removeprefix("/repos/")}
        samples = [run(), run(event="pull_request"), run(head_branch="feature"),
                   run(head_repository={"full_name": "other/SpiralGenesis"}),
                   run(path=".github/workflows/release.yml")]
        api.items = lambda path, field=None: samples if field else []
        metadata = feeds.public_metadata(api)
        self.assertEqual(metadata["SpiralGenesis"]["runs"], [samples[0]])
        self.assertEqual(metadata["SessionPulse"]["runs"], [])


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.api = FakeAPI()
        self.store = Store()
        self.key = "SpiralGenesis:release:30"
        self.events = [(self.key, "dev", feeds.payload("release", "details", "https://github.com"))]

    def test_pending_intent_precedes_send_and_confirmed_state_deduplicates(self):
        feeds.deliver(self.api, self.store, self.events, NOW, {"dev": "secret"})
        self.assertEqual(self.store.saved[0]["deliveries"][self.key]["status"], "pending")
        self.assertEqual(self.store.state["deliveries"][self.key]["message_id"], "123")
        feeds.deliver(self.api, self.store, self.events, NOW, {"dev": "secret"})
        self.assertEqual(len(self.api.calls), 1)
        self.assertNotIn("secret", json.dumps(self.store.saved))

    def test_unknown_delivery_never_automatically_retries(self):
        self.api.outcome = ("uncertain", None)
        for _ in range(2):
            with self.assertRaises(RuntimeError):
                feeds.deliver(self.api, self.store, self.events, NOW, {"dev": "secret"})
        self.assertEqual(len(self.api.calls), 1)

    def test_crash_pending_intent_blocks_replay(self):
        self.api.discord = lambda *args: (_ for _ in ()).throw(RuntimeError("crash"))
        with self.assertRaises(RuntimeError):
            feeds.deliver(self.api, self.store, self.events, NOW, {"dev": "secret"})
        self.api = FakeAPI()
        with self.assertRaises(RuntimeError):
            feeds.deliver(self.api, self.store, self.events, NOW, {"dev": "secret"})
        self.assertEqual(self.api.calls, [])

    def test_definite_rejection_has_backoff(self):
        self.api.outcome = ("retry", None)
        with self.assertRaises(RuntimeError):
            feeds.deliver(self.api, self.store, self.events, NOW, {"dev": "secret"})
        with self.assertRaises(RuntimeError):
            feeds.deliver(self.api, self.store, self.events, NOW, {"dev": "secret"})
        self.assertEqual(len(self.api.calls), 1)

    def test_failure_health_changes_only_after_confirmed_delivery(self):
        key = "SpiralGenesis:health:21:1:failed"
        feeds.deliver(self.api, self.store, [(key, "staff", {})], NOW, {"staff": "secret"})
        self.assertEqual(self.store.state["health"]["SpiralGenesis"], "failed")


class StateTests(unittest.TestCase):
    def test_contents_api_can_write_only_exact_state_branch_path_with_signed_identity(self):
        api = FakeAPI()
        calls = []
        def github(path, body=None):
            calls.append((path, body))
            if body is None:
                return {"sha": "old", "content": base64.b64encode(json.dumps(state()).encode()).decode()}
            return {"content": {"sha": "new"}}
        api.github = github
        store = feeds.StateStore(api)
        store.save()
        self.assertEqual(len(calls), 1)
        store.state["health"]["AntiSpeedrun"] = "failed"
        store.save()
        path, body = calls[-1]
        self.assertEqual(path, "/repos/Ninja6-MC/.github/contents/discord-feed-state.json")
        self.assertEqual(body["branch"], "chore/discord-feed-state")
        self.assertEqual(body["sha"], "old")
        self.assertEqual(body["author"]["email"], "bharathasl74185@gmail.com")
        self.assertEqual(body["author"], body["committer"])
        self.assertIn("Signed-off-by: Bharath <bharathasl74185@gmail.com>", body["message"])

    def test_state_schema_rejects_credentials_private_sources_and_payloads(self):
        for extra in ({"webhook": "secret"}, {"private": "other"}):
            with self.assertRaises(ValueError):
                feeds.validate_state(dict(state(), **extra))
        invalid = state()
        invalid["health"]["other"] = "failed"
        with self.assertRaises(ValueError):
            feeds.validate_state(invalid)

    def test_api_rejects_main_and_other_write_targets_before_network(self):
        api = feeds.API("unused")
        with self.assertRaises(ValueError):
            api.github("/repos/Ninja6-MC/.github/contents/discord-feed-state.json", {"branch": "main"})
        with self.assertRaises(ValueError):
            api.github("/repos/Ninja6-MC/SpiralGenesis/contents/file", {"branch": feeds.STATE_BRANCH})

    def test_discord_classifies_network_and_client_errors_without_resending(self):
        api = feeds.API("unused")
        url = "https://discord.com/api/webhooks/123/abc"
        with patch.object(api.opener, "open", side_effect=OSError("timeout")):
            self.assertEqual(api.discord(url, {}), ("uncertain", None))
        with patch.object(api.opener, "open", side_effect=urllib.error.HTTPError(url, 429, "rejected", {}, None)):
            self.assertEqual(api.discord(url, {}), ("retry", None))
        with patch.object(api.opener, "open", side_effect=urllib.error.HTTPError(url, 500, "error", {}, None)):
            self.assertEqual(api.discord(url, {}), ("uncertain", None))

    def test_digest_is_a_template_draft_without_release_body_or_commit_text(self):
        text = feeds.digest({"SpiralGenesis": {"runs": [run()], "releases": [release(body="untrusted")] }}, NOW)
        self.assertIn("Review before posting", text)
        self.assertNotIn("untrusted", text)


if __name__ == "__main__":
    unittest.main()
