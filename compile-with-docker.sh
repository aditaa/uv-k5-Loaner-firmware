#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
OUT_DIR="${SCRIPT_DIR}/compiled-firmware"
IMAGE_TAG="uvk5-loaner"

mkdir -p "${OUT_DIR}"

docker build -t "${IMAGE_TAG}" "${SCRIPT_DIR}"

docker run --rm \
  -v "${OUT_DIR}":/app/compiled-firmware \
  "${IMAGE_TAG}" \
  /bin/bash -lc "cd /app && make clean && make TARGET=loaner-firmware && cp loaner-firmware*.bin compiled-firmware/"
