#!/bin/bash
set -euo pipefail

if ! command -v clang-format >/dev/null 2>&1; then
	echo "clang-format not found on PATH" >&2
	exit 1
fi

# Determine the base to diff against. On PRs GitHub exposes GITHUB_BASE_REF.
if [[ -n "${GITHUB_BASE_REF:-}" ]]; then
	BASE_REF="origin/${GITHUB_BASE_REF}"
else
	BASE_REF="${1:-origin/main}"
fi

# Ensure the base ref is available locally.
git fetch --no-tags --depth=1 origin "${BASE_REF#origin/}" >/dev/null 2>&1 || true

DIFF=$(git diff --diff-filter=ACMRTUXB "${BASE_REF}"... -- '*.c' '*.h' | clang-format-diff -p1)

if [[ -n "${DIFF}" ]]; then
	echo "clang-format diff detected:"
	echo "${DIFF}"
	exit 1
fi

echo "clang-format check passed."
