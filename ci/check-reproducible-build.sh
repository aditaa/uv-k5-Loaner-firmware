#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
FIRST_BUILD="$(mktemp -d)"

cleanup() {
	rm -rf -- "${FIRST_BUILD}"
}
trap cleanup EXIT

: "${VERSION_SUFFIX:?VERSION_SUFFIX is required}"

cd "${ROOT}"

build_firmware() {
	make clean
	make TARGET=loaner-firmware VERSION_SUFFIX="${VERSION_SUFFIX}"
}

echo "Building reproducibility sample 1 of 2..."
build_firmware
cp loaner-firmware.bin loaner-firmware.packed.bin "${FIRST_BUILD}/"

echo "First-build hashes:"
sha256sum "${FIRST_BUILD}/loaner-firmware.bin" \
	"${FIRST_BUILD}/loaner-firmware.packed.bin"

echo "Building reproducibility sample 2 of 2..."
build_firmware

cmp "${FIRST_BUILD}/loaner-firmware.bin" loaner-firmware.bin
cmp "${FIRST_BUILD}/loaner-firmware.packed.bin" loaner-firmware.packed.bin

echo "Second-build hashes:"
sha256sum loaner-firmware.bin loaner-firmware.packed.bin
echo "Reproducibility check passed: raw and packed firmware are byte-identical."
