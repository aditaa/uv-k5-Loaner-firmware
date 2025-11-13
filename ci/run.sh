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

mkdir -p "${ARTIFACT_DIR}"
rm -f "${ARTIFACT_DIR}"/loaner-firmware*.bin

run_cppcheck

echo "Running unit tests..."
pytest -q

echo "Building firmware..."
make clean
make TARGET=loaner-firmware

BIN_SIZE=$(stat --format="%s" loaner-firmware.bin)
MAX_SIZE=${MAX_FIRMWARE_SIZE:-122880}
if (( BIN_SIZE > MAX_SIZE )); then
	echo "Firmware size ${BIN_SIZE} bytes exceeds limit ${MAX_SIZE} bytes" >&2
	exit 1
fi

echo "Firmware size: ${BIN_SIZE} bytes (limit ${MAX_SIZE})"

cp loaner-firmware*.bin "${ARTIFACT_DIR}/"
