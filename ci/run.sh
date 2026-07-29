#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
ARTIFACT_DIR="${ROOT}/compiled-firmware"
MODE="${CI_MODE:-full}"

cd "${ROOT}"

run_cppcheck() {
	echo "Running cppcheck lint..."
	cppcheck \
		--enable=warning,style \
		--std=c11 \
		--inline-suppr \
		--error-exitcode=1 \
		--suppress=missingIncludeSystem \
		--suppress=unmatchedSuppression \
		--suppress=unusedFunction \
		--suppress=invalidPrintfArgType_sint \
		--suppress=variableScope \
		--suppress=unsignedPositive \
		--suppress=badBitmaskCheck \
		--suppress=unusedStructMember \
		--suppress=constParameterPointer \
		--suppress=oppositeInnerCondition \
		--suppress=normalCheckLevelMaxBranches \
		--quiet \
		"${ROOT}/app" \
		"${ROOT}/audio.c" \
		"${ROOT}/bitmaps.c" \
		"${ROOT}/board.c" \
		"${ROOT}/dcs.c" \
		"${ROOT}/driver" \
		"${ROOT}/eeprom_validation.c" \
		"${ROOT}/functions.c" \
		"${ROOT}/helper" \
		"${ROOT}/misc.c" \
		"${ROOT}/radio.c" \
		"${ROOT}/scheduler.c" \
		"${ROOT}/settings.c" \
		"${ROOT}/ui" \
		"${ROOT}/version.c"
}

if [[ "${MODE}" == "cppcheck" ]]; then
	run_cppcheck
	exit 0
fi

: "${VERSION_SUFFIX:?VERSION_SUFFIX is required (set a 7-character value such as VERSION_SUFFIX=LNR2415 before running this script)}"

SOURCE_COMMIT="${SOURCE_COMMIT:-$(git rev-parse HEAD)}"
if [[ ! "${SOURCE_COMMIT}" =~ ^[0-9a-f]{40}$ ]]; then
	echo "SOURCE_COMMIT must be a full 40-character lowercase Git SHA" >&2
	exit 1
fi
SOURCE_DATE_EPOCH="${SOURCE_DATE_EPOCH:-$(git show -s --format=%ct "${SOURCE_COMMIT}")}"
if [[ ! "${SOURCE_DATE_EPOCH}" =~ ^[0-9]+$ ]]; then
	echo "SOURCE_DATE_EPOCH must be a non-negative integer" >&2
	exit 1
fi
export SOURCE_COMMIT SOURCE_DATE_EPOCH

mkdir -p "${ARTIFACT_DIR}"
rm -f \
	"${ARTIFACT_DIR}"/loaner-firmware-* \
	"${ARTIFACT_DIR}/loaner-firmware.bin" \
	"${ARTIFACT_DIR}/loaner-firmware.packed.bin"

echo "Checking C formatting..."
"${ROOT}/ci/check-clang-format.sh"

run_cppcheck

echo "Running unit tests..."
HOST_TESTS_REQUIRED=1 HOST_SANITIZERS=address,undefined pytest -q

echo "Build inputs:"
echo "  source commit: ${SOURCE_COMMIT}"
echo "  source date epoch: ${SOURCE_DATE_EPOCH}"
echo "  firmware suffix: ${VERSION_SUFFIX}"
echo "  container base: ${BUILD_CONTAINER_BASE:-native}"
echo "  package snapshot: ${BUILD_PACKAGE_SNAPSHOT:-native}"
python3 --version
arm-none-eabi-gcc --version | head -n 1
arm-none-eabi-ld --version | head -n 1

bash "${ROOT}/ci/check-reproducible-build.sh"

BIN_SIZE=$(stat --format="%s" loaner-firmware.bin)
MAX_SIZE=${MAX_FIRMWARE_SIZE:-122880}
if (( BIN_SIZE > MAX_SIZE )); then
	echo "Firmware size ${BIN_SIZE} bytes exceeds limit ${MAX_SIZE} bytes" >&2
	exit 1
fi

echo "Firmware size: ${BIN_SIZE} bytes (limit ${MAX_SIZE})"

BUNDLE_ARGS=(
	--suffix "${VERSION_SUFFIX}"
	--source-commit "${SOURCE_COMMIT}"
	--raw loaner-firmware.bin
	--packed loaner-firmware.packed.bin
	--output-dir "${ARTIFACT_DIR}"
)
VERIFY_ARGS=(
	--manifest "${ARTIFACT_DIR}/loaner-firmware-${VERSION_SUFFIX}.manifest.json"
	--expected-suffix "${VERSION_SUFFIX}"
)
if [[ -n "${RELEASE_TAG:-}" ]]; then
	BUNDLE_ARGS+=(--tag "${RELEASE_TAG}")
	VERIFY_ARGS+=(--expected-tag "${RELEASE_TAG}")
fi

echo "Creating verified artifact bundle..."
MANIFEST_PATH="$(python3 ci/release_artifacts.py bundle "${BUNDLE_ARGS[@]}")"
python3 ci/release_artifacts.py verify-bundle "${VERIFY_ARGS[@]}"
echo "Recorded build manifest:"
cat "${MANIFEST_PATH}"
