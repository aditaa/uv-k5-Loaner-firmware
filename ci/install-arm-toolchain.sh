#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TOOLCHAIN_VERSION="10.3-2021.10"
TOOLCHAIN_ARCHIVE="gcc-arm-none-eabi-${TOOLCHAIN_VERSION}-x86_64-linux.tar.bz2"
TOOLCHAIN_URL="https://developer.arm.com/-/media/Files/downloads/gnu-rm/${TOOLCHAIN_VERSION}/${TOOLCHAIN_ARCHIVE}?rev=78196d3461ba4c9089a67b5f33edf82a&revision=78196d34-61ba-4c90-89a6-7b5f33edf82a&hash=B94A380A17942218223CD08320496FB1"
CHECKSUM_FILE="${SCRIPT_DIR}/gcc-arm-none-eabi-${TOOLCHAIN_VERSION}.sha256"
DESTINATION="${1:-/opt}"
DOWNLOAD_DIR="$(mktemp -d)"

cleanup() {
	rm -rf -- "${DOWNLOAD_DIR}"
}
trap cleanup EXIT

mkdir -p "${DESTINATION}"
curl --fail --location --retry 3 --output "${DOWNLOAD_DIR}/${TOOLCHAIN_ARCHIVE}" \
	"${TOOLCHAIN_URL}"

(
	cd "${DOWNLOAD_DIR}"
	sha256sum --check "${CHECKSUM_FILE}"
)

tar -xjf "${DOWNLOAD_DIR}/${TOOLCHAIN_ARCHIVE}" -C "${DESTINATION}"

TOOLCHAIN_BIN="${DESTINATION}/gcc-arm-none-eabi-${TOOLCHAIN_VERSION}/bin"
if [[ -n "${GITHUB_PATH:-}" ]]; then
	echo "${TOOLCHAIN_BIN}" >> "${GITHUB_PATH}"
fi

"${TOOLCHAIN_BIN}/arm-none-eabi-gcc" --version | head -n 1
"${TOOLCHAIN_BIN}/arm-none-eabi-ld" --version | head -n 1
