#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
OUT_DIR="${SCRIPT_DIR}/compiled-firmware"
IMAGE_TAG="uvk5-loaner"

if [[ -z "${VERSION_SUFFIX:-}" ]]; then
  echo "VERSION_SUFFIX must be set (use a 7-character alphanumeric value, e.g. VERSION_SUFFIX=LNR2414 ./compile-with-docker.sh)" >&2
  exit 1
fi

mkdir -p "${OUT_DIR}"

rm -f "${OUT_DIR}"/loaner-firmware*.bin

docker build -t "${IMAGE_TAG}" "${SCRIPT_DIR}"

docker run --rm \
  -v "${OUT_DIR}":/app/compiled-firmware \
  -e VERSION_SUFFIX="${VERSION_SUFFIX}" \
  "${IMAGE_TAG}" \
  /bin/bash -lc "cd /app && chmod +x ci/run.sh && ./ci/run.sh"
