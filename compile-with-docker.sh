#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
OUT_DIR="${SCRIPT_DIR}/compiled-firmware"
IMAGE_TAG="uvk5-loaner"

if [[ -z "${VERSION_SUFFIX:-}" ]]; then
  echo "VERSION_SUFFIX must be set (use a 7-character alphanumeric value, e.g. VERSION_SUFFIX=LNR2415 ./compile-with-docker.sh)" >&2
  exit 1
fi
if [[ ! "${VERSION_SUFFIX}" =~ ^[A-Z0-9]{7}$ ]]; then
  echo "VERSION_SUFFIX must be exactly 7 uppercase alphanumeric characters" >&2
  exit 1
fi

SOURCE_COMMIT="${SOURCE_COMMIT:-$(git -C "${SCRIPT_DIR}" rev-parse HEAD)}"
RELEASE_TAG="${RELEASE_TAG:-}"

mkdir -p "${OUT_DIR}"

rm -f \
  "${OUT_DIR}"/loaner-firmware-* \
  "${OUT_DIR}/loaner-firmware.bin" \
  "${OUT_DIR}/loaner-firmware.packed.bin"

docker build -t "${IMAGE_TAG}" "${SCRIPT_DIR}"

docker run --rm \
  -v "${OUT_DIR}":/app/compiled-firmware \
  -e VERSION_SUFFIX="${VERSION_SUFFIX}" \
  -e SOURCE_COMMIT="${SOURCE_COMMIT}" \
  -e RELEASE_TAG="${RELEASE_TAG}" \
  "${IMAGE_TAG}" \
  /bin/bash -lc "cd /app && chmod +x ci/run.sh && ./ci/run.sh"
