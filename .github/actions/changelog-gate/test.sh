#!/usr/bin/env bash

set -euo pipefail

action_dir="$(cd "$(dirname "$0")" && pwd)"
test_dir="$(mktemp -d)"
trap 'rm -rf "$test_dir"' EXIT

run_gate() {
  local fixture="$1"
  local version="$2"
  local prerelease="$3"

  (
    cd "$fixture"
    CHANGELOG_GATE_VERSION="$version" \
      CHANGELOG_GATE_PRERELEASE="$prerelease" \
      bash "$action_dir/check.sh"
  )
}

pass_fixture="$test_dir/pass"
mkdir -p "$pass_fixture"
cat > "$pass_fixture/CHANGELOG.md" <<'EOF'
# Changelog

## [1.2.3]

- Ship the feature.

## [1.2.2]

- Previous release.
EOF
run_gate "$pass_fixture" 1.2.3 false

empty_fixture="$test_dir/empty"
mkdir -p "$empty_fixture"
cat > "$empty_fixture/CHANGELOG.md" <<'EOF'
# Changelog

## [1.2.3]

## [1.2.2]

- Previous release.
EOF
if run_gate "$empty_fixture" 1.2.3 false; then
  echo "Expected an empty stable changelog section to fail."
  exit 1
fi

unmatched_fixture="$test_dir/unmatched"
mkdir -p "$unmatched_fixture"
cat > "$unmatched_fixture/CHANGELOG.md" <<'EOF'
# Changelog

## [1.2.2]

- Previous release.
EOF
if run_gate "$unmatched_fixture" 1.2.3 false; then
  echo "Expected a missing stable changelog section to fail."
  exit 1
fi

missing_fixture="$test_dir/missing"
mkdir -p "$missing_fixture"
if run_gate "$missing_fixture" 1.2.3 false; then
  echo "Expected a missing stable changelog to fail."
  exit 1
fi

run_gate "$missing_fixture" 1.2.3-alpha.1 true

echo "Changelog gate tests passed."
