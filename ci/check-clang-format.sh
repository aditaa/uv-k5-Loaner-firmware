#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
REQUIREMENTS="${SCRIPT_DIR}/requirements-ci.txt"
MODE="check"
EXPORT_DIFF_FILE=""

if [[ "${1:-}" == "--fix" ]]; then
	MODE="fix"
	shift
elif [[ "${1:-}" == "--check" ]]; then
	shift
elif [[ "${1:-}" == "--export-diff" ]]; then
	if [[ -z "${2:-}" ]]; then
		echo "--export-diff requires an output path" >&2
		exit 1
	fi
	EXPORT_DIFF_FILE="$2"
	shift 2
fi

# Determine the base to diff against. On PRs GitHub exposes GITHUB_BASE_REF.
if [[ -n "${GITHUB_BASE_REF:-}" ]]; then
	BASE_REF="origin/${GITHUB_BASE_REF}"
else
	BASE_REF="${1:-origin/main}"
fi

cd "${ROOT}"

source_diff() {
	local MergeBase
	local Path
	local Status

	if [[ "${BASE_REF}" == origin/* ]]; then
		git fetch --no-tags origin "${BASE_REF#origin/}" >/dev/null 2>&1 || true
	fi

	if ! MergeBase="$(git merge-base "${BASE_REF}" HEAD)"; then
		echo "Unable to find a merge base for ${BASE_REF}; fetch the base branch and retry" >&2
		return 1
	fi

	git diff -U0 --no-color --relative --diff-filter=ACMRTUXB "${MergeBase}" -- '*.c' '*.h'
	while IFS= read -r Path; do
		Status=0
		git diff --no-index -U0 --no-color -- /dev/null "${Path}" || Status=$?
		if ((Status > 1)); then
			return "${Status}"
		fi
	done < <(git ls-files --others --exclude-standard -- '*.c' '*.h')
}

if [[ -n "${EXPORT_DIFF_FILE}" ]]; then
	source_diff > "${EXPORT_DIFF_FILE}"
	echo "Exported C source diff from ${BASE_REF} to ${EXPORT_DIFF_FILE}."
	exit 0
fi

FORMATTER="${CLANG_FORMAT_BIN:-clang-format}"
FORMAT_DIFF="${CLANG_FORMAT_DIFF_BIN:-clang-format-diff.py}"
EXPECTED_VERSION="$(sed -n 's/^clang-format==//p' "${REQUIREMENTS}")"

if [[ -z "${EXPECTED_VERSION}" ]]; then
	echo "Unable to read the pinned clang-format version from ${REQUIREMENTS}" >&2
	exit 1
fi

if ! command -v "${FORMATTER}" >/dev/null 2>&1; then
	echo "${FORMATTER} not found on PATH; install ${REQUIREMENTS}" >&2
	exit 1
fi

if ! command -v "${FORMAT_DIFF}" >/dev/null 2>&1; then
	echo "${FORMAT_DIFF} not found on PATH; install ${REQUIREMENTS}" >&2
	exit 1
fi

ACTUAL_VERSION="$("${FORMATTER}" --version)"
if [[ "${ACTUAL_VERSION}" != *"version ${EXPECTED_VERSION}"* ]]; then
	echo "Expected clang-format ${EXPECTED_VERSION}, got: ${ACTUAL_VERSION}" >&2
	exit 1
fi

format_diff() {
	if [[ -n "${CLANG_FORMAT_DIFF_FILE:-}" ]]; then
		cat -- "${CLANG_FORMAT_DIFF_FILE}"
	else
		source_diff
	fi |
		"${FORMAT_DIFF}" -p1 -binary "${FORMATTER}" "$@"
}

if [[ "${MODE}" == "fix" ]]; then
	format_diff -i
	echo "clang-format applied to changed C lines."
	exit 0
fi

DIFF="$(format_diff)"

if [[ -n "${DIFF}" ]]; then
	echo "clang-format diff detected:"
	echo "${DIFF}"
	exit 1
fi

echo "clang-format ${EXPECTED_VERSION} check passed for changed C lines."
