#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
OUT_DIR="${SCRIPT_DIR}/compiled-firmware"
IMAGE_TAG="uvk5-loaner"

if [[ -z "${VERSION_SUFFIX:-}" ]]; then
  echo "VERSION_SUFFIX must be set (use a 7-character alphanumeric value, e.g. VERSION_SUFFIX=LNR24C5 ./compile-with-docker.sh)" >&2
  exit 1
fi
if [[ ! "${VERSION_SUFFIX}" =~ ^[A-Z0-9]{7}$ ]]; then
  echo "VERSION_SUFFIX must be exactly 7 uppercase alphanumeric characters" >&2
  exit 1
fi

SOURCE_COMMIT="${SOURCE_COMMIT:-$(git -C "${SCRIPT_DIR}" rev-parse HEAD)}"
RELEASE_TAG="${RELEASE_TAG:-}"
if [[ ! "${SOURCE_COMMIT}" =~ ^[0-9a-f]{40}$ ]]; then
  echo "SOURCE_COMMIT must be a full 40-character lowercase Git SHA" >&2
  exit 1
fi

SOURCE_DATE_EPOCH="${SOURCE_DATE_EPOCH:-$(git -C "${SCRIPT_DIR}" show -s --format=%ct "${SOURCE_COMMIT}")}"
if [[ ! "${SOURCE_DATE_EPOCH}" =~ ^[0-9]+$ ]]; then
  echo "SOURCE_DATE_EPOCH must be a non-negative integer" >&2
  exit 1
fi

SUBMODULE_STATUS="$(git -C "${SCRIPT_DIR}" submodule status --recursive)"
if grep -Eq '^[-+]' <<< "${SUBMODULE_STATUS}"; then
  echo "Submodules must be initialized at their recorded commits before building" >&2
  echo "${SUBMODULE_STATUS}" >&2
  exit 1
fi

mkdir -p "${OUT_DIR}"

rm -f \
  "${OUT_DIR}"/loaner-firmware-* \
  "${OUT_DIR}/loaner-firmware.bin" \
  "${OUT_DIR}/loaner-firmware.packed.bin" \
  "${OUT_DIR}/.source-format.diff"

FORMAT_DIFF_FILE="${OUT_DIR}/.source-format.diff"
cleanup() {
  rm -f -- "${FORMAT_DIFF_FILE}"
}
trap cleanup EXIT

"${SCRIPT_DIR}/ci/check-clang-format.sh" --export-diff "${FORMAT_DIFF_FILE}"

docker build -t "${IMAGE_TAG}" "${SCRIPT_DIR}"

DOCKER_OUT_DIR="${OUT_DIR}"
if [[ "$(uname -s)" =~ ^(MINGW|MSYS|CYGWIN) ]]; then
  DOCKER_OUT_DIR="$(cygpath -w "${OUT_DIR}")"
fi

MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker run --rm \
  -v "${DOCKER_OUT_DIR}:/app/compiled-firmware" \
  -e CLANG_FORMAT_DIFF_FILE=compiled-firmware/.source-format.diff \
  -e VERSION_SUFFIX="${VERSION_SUFFIX}" \
  -e SOURCE_COMMIT="${SOURCE_COMMIT}" \
  -e SOURCE_DATE_EPOCH="${SOURCE_DATE_EPOCH}" \
  -e RELEASE_TAG="${RELEASE_TAG}" \
  "${IMAGE_TAG}" \
  bash -lc "cd /app && chmod +x ci/run.sh && ./ci/run.sh"
