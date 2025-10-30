#!/bin/bash
set -euo pipefail

ROOT="/app"
ARTIFACT_DIR="${ROOT}/compiled-firmware"

mkdir -p "${ARTIFACT_DIR}"
rm -f "${ARTIFACT_DIR}"/loaner-firmware*.bin

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
  ${ROOT}/app \
  ${ROOT}/audio.c \
  ${ROOT}/bitmaps.c \
  ${ROOT}/board.c \
  ${ROOT}/dcs.c \
  ${ROOT}/driver \
  ${ROOT}/functions.c \
  ${ROOT}/helper \
  ${ROOT}/misc.c \
  ${ROOT}/radio.c \
  ${ROOT}/scheduler.c \
  ${ROOT}/settings.c \
  ${ROOT}/ui \
  ${ROOT}/version.c

echo "Running unit tests..."
pytest -q

echo "Building firmware..."
make clean
make TARGET=loaner-firmware

cp loaner-firmware*.bin "${ARTIFACT_DIR}/"
