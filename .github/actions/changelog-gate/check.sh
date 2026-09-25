#!/usr/bin/env bash

set -euo pipefail

case "${CHANGELOG_GATE_PRERELEASE:-}" in
  true)
    echo "Prerelease ${CHANGELOG_GATE_VERSION:-unknown} does not require a changelog section."
    exit 0
    ;;
  false)
    ;;
  *)
    echo "::error::prerelease must be true or false."
    exit 1
    ;;
esac

if [ -z "${CHANGELOG_GATE_VERSION:-}" ]; then
  echo "::error::version is required."
  exit 1
fi

if [ ! -f CHANGELOG.md ]; then
  echo "::error::CHANGELOG.md is required for stable release ${CHANGELOG_GATE_VERSION}."
  exit 1
fi

if awk -v header="## [${CHANGELOG_GATE_VERSION}]" '
  index($0, header) == 1 { in_section = 1; next }
  in_section && /^## / { exit }
  in_section && /[^[:space:]]/ { has_content = 1 }
  END { exit has_content ? 0 : 1 }
' CHANGELOG.md; then
  echo "CHANGELOG.md contains a non-empty ${CHANGELOG_GATE_VERSION} section."
  exit 0
fi

echo "::error::CHANGELOG.md has no non-empty '## [${CHANGELOG_GATE_VERSION}]' section."
exit 1
