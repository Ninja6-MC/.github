#!/usr/bin/env python3
"""Check a Ninja6-MC repository against the mechanically-checkable standards.

Run from the root of the repository being checked. The register it validates against
lives in this repository (Ninja6-MC/.github) at `standards/`, so the caller has to say
where that checkout is:

    REGISTER_DIR=/path/to/.github/standards python3 check-standards.py

Checks implemented, and only these:

  N6-REPO-05  .github/standards-exceptions.yml exists, parses, and every entry carries
              all six required fields with a legal `type` and a real rule ID
  N6-REPO-02  any file in .github/ISSUE_TEMPLATE/ implies config.yml beside it
  N6-CI-01    .github/workflows/dco.yml calls the shared workflow instead of copying it
  N6-CI-04    .gitattributes pins every extension the repository actually contains
  N6-REPO-03  only the asset-sync App may touch assets/

The other rules in the register are deliberately absent. Branch naming, commit format
and PR titles are `reviewed`, not automatic, and a check that guesses at them would
produce false failures on exactly the edge cases a human handles well.

EXCEPTION-AWARE. A failure whose rule has an entry in the repository's
standards-exceptions.yml is downgraded to a notice and does not fail the run. That is
the whole point of the register: a recorded deviation is an exception, an unrecorded one
is a defect. The exception file's own validity (N6-REPO-05) cannot be excepted this way
- a malformed file would otherwise be able to excuse itself.

Exit codes: 0 clean or fully excepted, 1 unexcepted violations, 2 the checker itself
could not run. 2 is distinct on purpose - a broken checker must not read as a clean repo.
"""

import os
import re
import subprocess
import sys

try:
    import yaml
except ImportError:  # pragma: no cover - the runner always has it
    sys.stderr.write("PyYAML is required. On a GitHub runner it is preinstalled.\n")
    sys.exit(2)


# The reference every stub must carry. The `.github` segment appears twice because the
# repository is itself named `.github` - see N6-CI-02. Getting this wrong fails the run
# at startup with zero jobs, which is why it is matched exactly rather than loosely.
SHARED_DCO = "Ninja6-MC/.github/.github/workflows/dco.yml"

# The author of the asset-sync App's commits. N6-REPO-03 exists to stop hand edits to
# assets/, not to stop the pipeline that owns it.
SYNC_APP_NAME = "ninja6-asset-sync[bot]"

# repo-layout.md, N6-CI-04: "pin to eol=lf every extension the repository actually
# contains from ...; pin Windows batch files to eol=crlf; and mark *.png, *.jar and
# *.zip as binary." This list is that sentence, and must not drift from it.
WANT_LF = (".sh", ".yml", ".yaml", ".md", ".svg", ".mjs")
WANT_CRLF = (".bat",)
WANT_BINARY = (".png", ".jar", ".zip")


class Finding:
    """One rule violation, before it is known whether an exception covers it."""

    def __init__(self, rule, summary, detail=""):
        self.rule = rule
        self.summary = summary
        self.detail = detail
        self.excepted_by = None


def git(*args):
    """Run git in the repository under test and return stdout, or None on failure."""
    try:
        out = subprocess.run(
            ("git",) + args, capture_output=True, check=True
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return out.decode("utf-8", "replace")


def load_yaml(path):
    """Return (data, error). Reads bytes and decodes explicitly: a Windows-authored file
    can carry a BOM, and yaml.safe_load on a str that starts with one fails with a
    message about the first character rather than about the BOM."""
    try:
        with open(path, "rb") as fh:
            raw = fh.read()
    except FileNotFoundError:
        return None, "file not found"
    except OSError as exc:
        return None, str(exc)
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        return None, "not valid UTF-8: %s" % exc
    try:
        return yaml.safe_load(text), None
    except yaml.YAMLError as exc:
        return None, "does not parse as YAML: %s" % exc


def known_rule_ids(register_dir):
    """Every rule ID the register actually assigns.

    Parsed out of standards/README.md rather than restated here, because the register is
    the single source of truth and a second copy would drift. `N6-CMD-*` and `N6-REL-*`
    are reserved but unassigned; they carry a literal asterisk in the register and so
    cannot match this pattern, which is exactly the behaviour wanted - citing one must
    be an error until those areas are populated.
    """
    path = os.path.join(register_dir, "README.md")
    try:
        with open(path, "rb") as fh:
            text = fh.read().decode("utf-8-sig")
    except OSError:
        return None
    return set(re.findall(r"\bN6-[A-Z]+-\d{2}\b", text))


# --------------------------------------------------------------------------------------
# N6-REPO-05 - the exceptions file itself
# --------------------------------------------------------------------------------------

REQUIRED_FIELDS = ("rule", "type", "reason", "approved_by", "approved_on", "revisit_by")
LEGAL_TYPES = ("permanent", "transitional")

# Forward slashes throughout: these strings end up in error messages, and a
# backslash path would be wrong for every reader of the log. os.path.exists
# accepts them on Windows too, so nothing is lost by writing them portably.
EXCEPTIONS_PATH = ".github/standards-exceptions.yml"


def check_exceptions_file(repo, valid_rules):
    """Validate the exceptions file and return (findings, exceptions_by_rule).

    The second value drives every other check, so this runs first and its findings are
    never themselves excepted.
    """
    findings = []

    if not os.path.exists(EXCEPTIONS_PATH):
        findings.append(Finding(
            "N6-REPO-05",
            "%s is missing" % EXCEPTIONS_PATH,
            "Every repository carries this file, even with an empty `exceptions` list - "
            "an absent file is indistinguishable from an oversight, an empty one is a "
            "statement. Schema and a worked example are in standards/README.md section 3.\n"
            "A repository that has not adopted the register yet is not in breach, but "
            "adding this workflow IS the adoption, so the file has to come with it.",
        ))
        return findings, {}

    data, err = load_yaml(EXCEPTIONS_PATH)
    if err:
        findings.append(Finding("N6-REPO-05", "%s %s" % (EXCEPTIONS_PATH, err)))
        return findings, {}

    if not isinstance(data, dict):
        findings.append(Finding(
            "N6-REPO-05", "%s must be a mapping with `repo` and `exceptions` keys" % EXCEPTIONS_PATH))
        return findings, {}

    declared = data.get("repo")
    if declared != repo:
        findings.append(Finding(
            "N6-REPO-05",
            "`repo:` says %r but this repository is %r" % (declared, repo),
            "A copied file that still names the repository it was copied from is the "
            "usual cause, and it makes the register's own audit trail wrong.",
        ))

    if "exceptions" not in data:
        findings.append(Finding(
            "N6-REPO-05", "%s has no `exceptions` key" % EXCEPTIONS_PATH,
            "Use `exceptions: []` to state that the repository conforms."))
        return findings, {}

    entries = data["exceptions"]
    if entries is None:
        # `exceptions:` with nothing after it. Distinct from `exceptions: []`, and the
        # difference is invisible on screen, so say which one was meant.
        findings.append(Finding(
            "N6-REPO-05", "`exceptions:` is empty rather than an empty list",
            "Write `exceptions: []`. A bare `exceptions:` parses as null, which reads as "
            "an unfinished edit rather than as a statement of conformance."))
        return findings, {}

    if not isinstance(entries, list):
        findings.append(Finding(
            "N6-REPO-05", "`exceptions` must be a list, got %s" % type(entries).__name__))
        return findings, {}

    by_rule = {}
    for i, entry in enumerate(entries):
        where = "exceptions[%d]" % i
        if not isinstance(entry, dict):
            findings.append(Finding("N6-REPO-05", "%s is not a mapping" % where))
            continue

        missing = [f for f in REQUIRED_FIELDS if f not in entry or entry[f] in (None, "")]
        if missing:
            findings.append(Finding(
                "N6-REPO-05",
                "%s is missing required field(s): %s" % (where, ", ".join(missing)),
                "All six of %s are required - see standards/README.md section 3."
                % ", ".join(REQUIRED_FIELDS),
            ))

        rule = entry.get("rule")
        if rule and valid_rules is not None and rule not in valid_rules:
            reserved = isinstance(rule, str) and re.match(r"^N6-(CMD|REL)-", rule)
            findings.append(Finding(
                "N6-REPO-05",
                "%s cites %r, which the register does not assign" % (where, rule),
                "N6-CMD-* and N6-REL-* are reserved but unassigned. Do not cite an "
                "identifier from either area - there is nothing behind it yet."
                if reserved else
                "Rule IDs are permanent and are never renumbered. Check "
                "standards/README.md section 2 for the real identifier.",
            ))

        kind = entry.get("type")
        if kind is not None and kind not in LEGAL_TYPES:
            findings.append(Finding(
                "N6-REPO-05",
                "%s has type %r, expected `permanent` or `transitional`" % (where, kind),
                "`permanent` means the repository CANNOT comply and no work would change "
                "that. `transitional` means it can and does not yet. Keeping the two "
                "apart is the entire point of the field.",
            ))

        # A date, never the string `never`. An expired revisit_by does not fail the
        # build - it is the agenda for the next standards review - but an unparseable
        # one means nobody can tell whether it has expired.
        for field in ("approved_on", "revisit_by"):
            value = entry.get(field)
            if value is None:
                continue
            if not _is_date(value):
                findings.append(Finding(
                    "N6-REPO-05",
                    "%s has %s: %r, which is not a date" % (where, field, value),
                    "Use an unquoted ISO date, e.g. 2026-11-19. `never` is not allowed: "
                    "a permanent exception that keeps being re-approved is a sign the "
                    "rule is wrong, and the date is what surfaces that.",
                ))

        if rule:
            by_rule.setdefault(rule, entry)

    return findings, by_rule


def _is_date(value):
    """True for a real date. PyYAML gives datetime.date for an unquoted ISO date; a
    quoted one arrives as str and is accepted if it parses."""
    if hasattr(value, "isoformat"):
        return True
    if isinstance(value, str):
        return bool(re.match(r"^\d{4}-\d{2}-\d{2}$", value.strip()))
    return False


# --------------------------------------------------------------------------------------
# N6-REPO-02 - issue templates inherit per directory
# --------------------------------------------------------------------------------------

def check_issue_templates():
    d = ".github/ISSUE_TEMPLATE"
    if not os.path.isdir(d):
        return []
    present = sorted(f for f in os.listdir(d) if not f.startswith("."))
    if not present:
        return []
    if "config.yml" in present or "config.yaml" in present:
        return []
    return [Finding(
        "N6-REPO-02",
        "%s defines %s but no config.yml" % (d, ", ".join(present)),
        "Issue templates inherit per DIRECTORY, not per file. Defining any file here "
        "means this repository inherits none of the org set, config.yml included - so "
        "blank issues stay enabled and the security contact link disappears from the "
        "chooser. Nothing reports this; the repository looks fine and only the chooser "
        "is wrong. The file to add is in standards/repo-layout.md under N6-REPO-02.",
    )]


# --------------------------------------------------------------------------------------
# N6-CI-01 - call the shared DCO workflow, do not copy it
# --------------------------------------------------------------------------------------

def check_dco(repo):
    path = ".github/workflows/dco.yml"
    if not os.path.exists(path):
        return [Finding(
            "N6-CI-01", "%s is missing" % path,
            "Copy templates/dco-stub.yml from Ninja6-MC/.github. DCO is enforced on "
            "every repository in the organisation.")]

    data, err = load_yaml(path)
    if err:
        return [Finding("N6-CI-01", "%s %s" % (path, err))]
    if not isinstance(data, dict):
        return [Finding("N6-CI-01", "%s is not a workflow mapping" % path)]

    jobs = data.get("jobs") or {}

    # This repository satisfies the rule by HOSTING the workflow rather than calling it.
    # ci.md is explicit that this is compliance, not an exception. Its dco.yml carries
    # both workflow_call and pull_request, so its own PRs run the same script every
    # other repository calls.
    if repo == ".github":
        # `on:` is the YAML 1.1 boolean True once parsed - PyYAML reads a bare `on` key
        # as a boolean, not a string. Both spellings are checked because a quoted "on"
        # in the source would arrive as the string.
        triggers = data.get("on", data.get(True)) or {}
        names = set(triggers) if isinstance(triggers, dict) else set(
            triggers if isinstance(triggers, list) else [triggers])
        if "workflow_call" not in names:
            return [Finding(
                "N6-CI-01",
                "this repository hosts dco.yml but it has no `workflow_call` trigger",
                "Hosting the workflow is how .github satisfies N6-CI-01, but only while "
                "the workflow is actually callable. Without workflow_call every other "
                "repository's stub fails at startup with zero jobs.")]
        return []

    for job in jobs.values():
        if not isinstance(job, dict):
            continue
        uses = job.get("uses")
        if not isinstance(uses, str):
            continue
        ref = uses.split("@", 1)[0]
        if ref == SHARED_DCO:
            return []
        # The single-.github mistake, called out by name because the resulting failure
        # says nothing useful: the run starts with zero jobs.
        if ref.replace("/.github/.github/", "/.github/") == SHARED_DCO.replace(
                "/.github/.github/", "/.github/"):
            return [Finding(
                "N6-CI-01",
                "%s references %r" % (path, uses),
                "The `.github` segment must appear TWICE - once as the repository name "
                "and once as the directory: %s@main. Written once it resolves to "
                "workflows/dco.yml, which is not a valid workflow location, and the run "
                "fails at startup with zero jobs and no error that points at the cause "
                "(N6-CI-02)." % SHARED_DCO)]

    return [Finding(
        "N6-CI-01",
        "%s does not call the shared workflow" % path,
        "A local copy is a violation even when its contents are correct, because a fix "
        "to the shared workflow never reaches it. Replace the file with "
        "templates/dco-stub.yml. Note this renames the reported check from "
        "`Check Sign-off` to `dco / Check Sign-off`, so if the old name is in a required "
        "list, change both together or every open PR blocks forever (N6-CI-03).")]


# --------------------------------------------------------------------------------------
# N6-CI-06 / N6-CI-07 / N6-CI-08 - workflow hardening
# --------------------------------------------------------------------------------------

SHA_RE = re.compile(r"@[0-9a-f]{40}$")
ORG_REUSABLE = "Ninja6-MC/.github/"


def _workflow_files():
    d = os.path.join(".github", "workflows")
    if not os.path.isdir(d):
        return []
    return [os.path.join(d, f) for f in sorted(os.listdir(d))
            if f.endswith((".yml", ".yaml"))]


def _triggers(data):
    """`on:` parses as the YAML 1.1 boolean True. Both spellings are checked."""
    raw = data.get("on", data.get(True)) or {}
    if isinstance(raw, dict):
        return set(raw)
    if isinstance(raw, list):
        return set(raw)
    return {raw} if raw else set()


def check_workflow_hardening():
    findings = []
    for path in _workflow_files():
        data, err = load_yaml(path)
        if err:
            findings.append(Finding("N6-CI-07", "%s %s" % (path, err)))
            continue
        if not isinstance(data, dict):
            continue

        jobs = data.get("jobs") or {}
        reusable = "workflow_call" in _triggers(data)

        # ---- N6-CI-07: an explicit grant, at either level -----------------------------
        if "permissions" not in data:
            ungranted = [n for n, j in jobs.items()
                         if isinstance(j, dict) and "permissions" not in j]
            if ungranted:
                findings.append(Finding(
                    "N6-CI-07",
                    "%s declares no permissions, and neither do: %s"
                    % (path, ", ".join(sorted(ungranted))),
                    "A workflow with no `permissions:` runs on the repository default "
                    "grant. Declare one at workflow level, or - for a reusable workflow "
                    "whose job needs more than a workflow-level cap would allow - on the "
                    "job. A workflow-level grant CAPS a called job rather than being "
                    "replaced by it, which is why scorecard.yml declares its own on the "
                    "job and carries no top-level block."))
        elif reusable:
            # A cap is fine until a job needs more than it. That combination is the
            # startup_failure this rule exists to prevent: no job, no annotation.
            top = data.get("permissions")
            if isinstance(top, dict):
                for n, j in jobs.items():
                    if not isinstance(j, dict):
                        continue
                    jp = j.get("permissions")
                    if not isinstance(jp, dict):
                        continue
                    wider = [k for k, v in jp.items()
                             if v == "write" and top.get(k) != "write"]
                    if wider:
                        findings.append(Finding(
                            "N6-CI-07",
                            "%s is reusable, caps %s at the workflow level, and job %r "
                            "asks for: %s" % (path, sorted(top), n, ", ".join(sorted(wider))),
                            "In a CALLED workflow the workflow-level grant caps the job "
                            "instead of being replaced by it, so this combination fails "
                            "at startup with no job and nothing retrievable through the "
                            "API. Drop the top-level block and grant on the job."))

        for name, job in jobs.items():
            if not isinstance(job, dict):
                continue

            steps = job.get("steps") or []
            uses_refs = [job["uses"]] if isinstance(job.get("uses"), str) else []
            uses_refs += [s["uses"] for s in steps
                          if isinstance(s, dict) and isinstance(s.get("uses"), str)]

            # ---- N6-CI-06: pinned to a SHA -------------------------------------------
            for ref in uses_refs:
                if ref.startswith(ORG_REUSABLE):
                    # This organisation's own reusable workflows stay on @main
                    # deliberately; pinning them would defeat maintaining the checks in
                    # one place, and they are not third-party code.
                    continue
                if not SHA_RE.search(ref):
                    findings.append(Finding(
                        "N6-CI-06",
                        "%s job %r uses %r, which is not a commit SHA" % (path, name, ref),
                        "A tag can be repointed at new code with no diff, no review and "
                        "no notification. Pin to the 40-character commit SHA with the "
                        "version in a trailing comment. Check whether the tag is "
                        "annotated first - on an annotated tag the ref's object.sha is "
                        "the tag object and pinning to it fails; dereference through "
                        "/git/tags/{sha}. Pin only alongside .github/dependabot.yml "
                        "(N6-CI-06), or the pin goes stale in silence."))

            # ---- N6-CI-08: no persisted credentials ----------------------------------
            for step in steps:
                if not isinstance(step, dict):
                    continue
                if not str(step.get("uses", "")).startswith("actions/checkout@"):
                    continue
                with_ = step.get("with") or {}
                if "token" in with_:
                    # Passing a token IS the declaration that this checkout exists in
                    # order to push. brand/sync-assets.yml is the case.
                    continue
                if with_.get("persist-credentials") is not False:
                    findings.append(Finding(
                        "N6-CI-08",
                        "%s job %r checks out without `persist-credentials: false`"
                        % (path, name),
                        "actions/checkout writes the job token into .git/config by "
                        "default, where every later step can read it - including a "
                        "third-party action. Set persist-credentials: false unless this "
                        "checkout performs an authenticated git operation, in which case "
                        "it should pass an explicit `token:` instead."))

    return findings


# --------------------------------------------------------------------------------------
# N6-REL-01 - a repository that can publish a release documents how
# --------------------------------------------------------------------------------------

RELEASE_ACTIONS = ("softprops/action-gh-release",)


def _publishes_releases():
    """Does any workflow here have the capability to publish a release?

    The trigger is the CAPABILITY, not a filename: renaming release.yml exempts nothing,
    and a repository that has never cut a tag is covered the moment it could.
    """
    for path in _workflow_files():
        data, err = load_yaml(path)
        if err or not isinstance(data, dict):
            continue

        # A version-tag trigger. `on:` parses as boolean True; see _triggers.
        raw = data.get("on", data.get(True))
        if isinstance(raw, dict):
            push = raw.get("push")
            if isinstance(push, dict) and push.get("tags"):
                return path

        for job in (data.get("jobs") or {}).values():
            if not isinstance(job, dict):
                continue
            for step in (job.get("steps") or []):
                if not isinstance(step, dict):
                    continue
                uses = str(step.get("uses", ""))
                if uses.startswith(RELEASE_ACTIONS):
                    return path
                run = step.get("run")
                if isinstance(run, str) and "gh release create" in run:
                    return path
    return None


def check_release_docs():
    where = _publishes_releases()
    if not where:
        # Publishes nothing, so the rule does not apply. A repository may still carry the
        # files - SessionPulse documents a process it has not yet used, which is foresight
        # rather than a violation.
        return []

    missing = [f for f in ("RELEASE_PROCESS.md", "CHANGELOG.md") if not os.path.exists(f)]
    if not missing:
        return []

    return [Finding(
        "N6-REL-01",
        "%s can publish a release, but %s %s missing"
        % (where, " and ".join(missing), "is" if len(missing) == 1 else "are"),
        "A repository that can publish a release documents how. RELEASE_PROCESS.md is for "
        "the person cutting it - what the version promises, which tag produces which "
        "channel, what must be true first. CHANGELOG.md is for the person receiving it, "
        "and generated release notes are not a substitute: they list merged pull request "
        "titles, which is what work happened rather than what changed. Start from "
        "templates/release-process.template and see standards/releases.md.")]


# --------------------------------------------------------------------------------------
# N6-CI-04 - line endings
# --------------------------------------------------------------------------------------

def check_gitattributes():
    """Ask git what it will actually do, rather than reading .gitattributes as text.

    `git check-attr` resolves blanket rules, pattern precedence and macros the same way
    a real checkout does. Grepping the file for patterns would miss a repository that
    pins everything with `* text=auto eol=lf` - which is a correct way to satisfy the
    rule - and would also be fooled by a later pattern overriding an earlier one.
    """
    listing = git("ls-files", "-z")
    if listing is None:
        return [Finding("N6-CI-04", "could not list tracked files")]

    tracked = [p for p in listing.split("\0") if p]
    if not tracked:
        return []

    # One representative per extension is enough: attributes are matched by pattern, so
    # if the pattern covers one .yml it covers them all. Sorted for a stable message.
    sample = {}
    for path in tracked:
        ext = os.path.splitext(path)[1].lower()
        if ext and ext not in sample:
            sample[ext] = path

    findings = []

    def attr(name, paths):
        out = git("check-attr", name, "--", *paths)
        if out is None:
            return {}
        got = {}
        for line in out.splitlines():
            # `path: attr: value`, and a path may itself contain ": " - split from the
            # right so a colon in a filename cannot shift the fields.
            head, _, value = line.rpartition(": ")
            path, _, _attr = head.rpartition(": ")
            got[path] = value
        return got

    def want(exts, attr_name, expected, human):
        paths = [sample[e] for e in exts if e in sample]
        if not paths:
            return
        got = attr(attr_name, paths)
        for path in paths:
            if got.get(path) != expected:
                findings.append(Finding(
                    "N6-CI-04",
                    "%s is not pinned to %s" % (path, human),
                    "git resolves `%s` to %r for this path. Without the pin, a clone "
                    "with core.autocrlf=true (the Git for Windows default) rewrites the "
                    "file on checkout. templates/gitattributes.template is the canonical "
                    "starting point." % (attr_name, got.get(path)),
                ))

    want(WANT_LF, "eol", "lf", "eol=lf")
    want(WANT_CRLF, "eol", "crlf", "eol=crlf")
    want(WANT_BINARY, "binary", "set", "binary")

    return findings


# --------------------------------------------------------------------------------------
# N6-REPO-03 - assets/ is machine-managed
# --------------------------------------------------------------------------------------

def check_assets(base, head):
    """Only the sync App may touch assets/.

    Scoped to the commits in this pull request. Checking the whole history would flag
    every historical hand edit forever, which is noise rather than a finding - the rule
    is about what is landing now.
    """
    if not base or not head:
        # No pull_request payload. Not a failure: the other four checks are meaningful
        # on any event, and this one simply has nothing to look at.
        return []

    revs = git("rev-list", "--no-merges", "%s..%s" % (base, head))
    if revs is None:
        return [Finding("N6-REPO-03", "could not walk %s..%s" % (base, head))]

    findings = []
    for sha in revs.split():
        touched = git("diff-tree", "--no-commit-id", "--name-only", "-r", sha)
        if not touched:
            continue
        paths = [p for p in touched.split() if p == "assets" or p.startswith("assets/")]
        if not paths:
            continue
        author = (git("log", "-1", "--format=%an", sha) or "").strip()
        if author == SYNC_APP_NAME:
            continue
        subject = (git("log", "-1", "--format=%s", sha) or "").strip()
        findings.append(Finding(
            "N6-REPO-03",
            "%s (%s) edits assets/ but is authored by %r" % (sha[:8], subject, author),
            "assets/ is delivered by the sync pipeline in `brand` and is never hand "
            "edited. A hand edit is not rejected by the pipeline - it survives until the "
            "next sync and is then silently overwritten. To change what arrives, change "
            "brand/export/, or change `dest` for this repository in "
            "brand/.github/sync-assets.json. Files touched: %s" % ", ".join(paths),
        ))

    return findings


# --------------------------------------------------------------------------------------
# Reporting
# --------------------------------------------------------------------------------------

def emit(findings, summary_path):
    """Write GitHub annotations to stdout and a table to the job summary."""
    failed = [f for f in findings if not f.excepted_by]
    excused = [f for f in findings if f.excepted_by]

    for f in failed:
        detail = (" " + f.detail.replace("\n", " ")) if f.detail else ""
        print("::error title=%s::%s%s" % (f.rule, f.summary, detail))
    for f in excused:
        print("::notice title=%s (excepted)::%s - covered by a %s exception in "
              "standards-exceptions.yml" % (f.rule, f.summary, f.excepted_by))

    lines = ["## Standards", ""]
    if not findings:
        lines.append("No violations. This repository conforms to every mechanically "
                     "checked rule in the register.")
    else:
        if failed:
            lines += ["### Violations", ""]
            for f in failed:
                lines.append("* **`%s`** - %s" % (f.rule, f.summary))
                if f.detail:
                    lines.append("  <br>%s" % f.detail.replace("\n", "<br>"))
            lines.append("")
        if excused:
            lines += ["### Excepted", "",
                      "Recorded in `.github/standards-exceptions.yml`, so these do not "
                      "fail the run.", ""]
            for f in excused:
                lines.append("* **`%s`** (%s) - %s" % (f.rule, f.excepted_by, f.summary))
            lines.append("")
        lines.append("Register: <https://github.com/Ninja6-MC/.github/blob/main/standards/README.md>")

    text = "\n".join(lines) + "\n"
    print()
    print(text)
    if summary_path:
        try:
            with open(summary_path, "a", encoding="utf-8") as fh:
                fh.write(text)
        except OSError:
            pass

    return failed


def main():
    register_dir = os.environ.get("REGISTER_DIR")
    if not register_dir or not os.path.isdir(register_dir):
        sys.stderr.write(
            "REGISTER_DIR must point at the standards/ directory of a Ninja6-MC/.github "
            "checkout. Got %r.\n" % register_dir)
        return 2

    full = os.environ.get("REPO", "")
    repo = full.split("/")[-1] if full else os.path.basename(os.getcwd())

    valid_rules = known_rule_ids(register_dir)
    if not valid_rules:
        sys.stderr.write(
            "Could not read any rule IDs from %s/README.md. Refusing to run rather than "
            "passing everything by accident.\n" % register_dir)
        return 2

    print("Checking %s against %d assigned rule IDs.\n" % (repo, len(valid_rules)))

    findings, exceptions = check_exceptions_file(repo, valid_rules)

    # Everything from here on can be excepted. The exceptions file's own validity cannot
    # be, which is why those findings were gathered first and are not passed through the
    # loop below.
    others = []
    others += check_issue_templates()
    others += check_dco(repo)
    others += check_gitattributes()
    others += check_workflow_hardening()
    others += check_release_docs()
    others += check_assets(os.environ.get("BASE_SHA"), os.environ.get("HEAD_SHA"))

    for f in others:
        entry = exceptions.get(f.rule)
        if entry:
            f.excepted_by = entry.get("type", "recorded")

    failed = emit(findings + others, os.environ.get("GITHUB_STEP_SUMMARY"))

    if failed:
        print("%d unexcepted violation(s)." % len(failed))
        print("Fix them, or record an exception in .github/standards-exceptions.yml "
              "with a reason, an approver and a revisit date - see standards/README.md "
              "section 3.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
