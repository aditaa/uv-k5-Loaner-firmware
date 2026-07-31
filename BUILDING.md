# Building the Loaner Firmware

This document covers local builds, validation, firmware packing, and releases.
The default feature choices and rules for removing optional code are recorded
in [`docs/feature-inventory.md`](docs/feature-inventory.md).

## Prerequisites

- Docker for the recommended build path.
- For native builds: ARM GCC 10.3.1 on `PATH`, GNU Make, and Python 3.
- For native validation: `cppcheck`, `shellcheck`, and the pinned Python tools from `ci/requirements-ci.txt`.

## Docker Build (recommended)

Run the complete validation and build pipeline with an exact seven-character uppercase alphanumeric suffix:

```sh
VERSION_SUFFIX=LNR24C5 ./compile-with-docker.sh
```

From Windows Command Prompt with Git for Windows installed, run the same
pipeline through the batch wrapper:

```bat
set VERSION_SUFFIX=LNR24C5
compile-with-docker.bat
```

PowerShell users can set `$env:VERSION_SUFFIX = "LNR24C5"` and then run
`.\compile-with-docker.bat`.

The wrapper runs the formatting check, cppcheck, pytest, and two clean ARM builds. The two raw images and two packed images must be byte-identical before it writes a verified bundle to `compiled-firmware/`:

- `loaner-firmware-LNR24C5.bin`
- `loaner-firmware-LNR24C5.packed.bin`
- `loaner-firmware-LNR24C5.manifest.json`
- `loaner-firmware-LNR24C5.sha256`

The manifest records file sizes and hashes, the source commit, firmware identifiers, and build-tool versions. The checksum file covers both images and the manifest. The Docker base, dated Arch package repository, Python packages, Arm archive checksum, and GitHub Actions are pinned; see `ci/dependencies.md` for the reviewed values and update procedure.

## Native Build (optional)

```sh
make clean
make TARGET=loaner-firmware VERSION_SUFFIX=LNR24C5
```

This creates `loaner-firmware.bin` and the required `loaner-firmware.packed.bin`. Packing is fail-closed: an invalid suffix, undersized input, packer failure, or missing packed image fails the build. When `VERSION_SUFFIX` is omitted, Make reads the root `VERSION_SUFFIX` file.

## Packing and Verifying an Image

```sh
python3 fw-pack.py pack loaner-firmware.bin LNR24C5 loaner-firmware.packed.bin
python3 fw-pack.py verify loaner-firmware.packed.bin LNR24C5
```

The verifier checks the XMODEM CRC, `*OEFW-` metadata prefix, exact embedded suffix, and metadata padding. The raw firmware must be at least 8192 bytes so metadata is inserted at the required offset.

## Running Checks

The Docker wrapper is the canonical full check. Native equivalents are:

```sh
python -m pip install -r ci/requirements-ci.txt
ci/check-clang-format.sh
CI_MODE=cppcheck ci/run.sh
pytest -q
VERSION_SUFFIX=LNR24C5 ci/run.sh
```

GitHub Actions runs tests under Python 3.10.18 and 3.12.11, checks CHIRP compatibility, runs CodeQL, and performs the Docker firmware build. Docker builds export the changed-line formatting diff on the host and mount it read-only, so Git history never enters the image context. Keep the firmware below `MAX_FIRMWARE_SIZE` (122880 bytes by default).

See `docs/host-testing.md` for the pure-logic/hardware boundary, reusable fake
platform adapters, sanitizer mode, and the command for running one host C test
module.

## Release Version Mapping

Release tags must use `vYY.MM[.PATCH]`. They map to the seven-character suffix `LNRYYMP`, where month and patch each use one base-36 digit (`0-9`, then `A-Z`):

| Release tag | Firmware suffix |
| --- | --- |
| `v24.03` | `LNR2430` |
| `v24.10.5` | `LNR24A5` |
| `v24.12.35` | `LNR24CZ` |

An omitted patch maps to `0`. Months outside 1-12, patches above 35, leading-zero patches, and malformed tags are rejected.

Derive the suffix instead of calculating it manually:

```sh
python3 ci/release_artifacts.py tag-to-suffix v24.10.5
```

Before tagging, write the resulting value to the root `VERSION_SUFFIX` file and merge that change. The release workflow requires the file, tag, packed metadata, display banner, UART identifier, artifact names, and manifest to agree.

## Release Checklist

The concise software, hardware, and publishing gate is maintained in
[`docs/release-checklist.md`](docs/release-checklist.md). The version/tag steps
below provide the detailed command sequence.

1. Create a release branch from current `main`.
2. Pick a `vYY.MM[.PATCH]` tag and derive its suffix.
3. Update `VERSION_SUFFIX`, build with that suffix, and run all checks, including the two-build hash comparison.
4. Flash the packed image with the
   [Egzumer UV Tools web flasher](https://egzumer.github.io/uvtools/) and confirm
   the displayed version on hardware.
5. Merge the release preparation PR.
6. Tag the exact merge commit and push the annotated tag:

   ```sh
   git tag -a v24.10.5 -m "Loaner firmware v24.10.5"
   git push origin v24.10.5
   ```

7. Confirm the automated release contains the raw image, packed image, JSON manifest, and SHA-256 file.

The release workflow only triggers for version-shaped tags, validates the full tag syntax, rebuilds the tagged commit, verifies the bundle before upload, and refuses to overwrite an existing GitHub release.

## Feature Toggles

Feature flags live near the top of `Makefile`. The loaner build keeps AIRCOPY, ALARM, FM radio, NOAA, TX1750, and the SRAM overlay disabled by default. Run `make clean` before comparing size after changing flags.

## Transmit Policy

The loaner build does not enforce the legacy regional `F LOCK`, `200TX`, `350TX`, `350EN`, or `500TX` policy switches. It still blocks the unsupported 76-108 MHz gap, frequencies outside the defined 50-76 MHz and 108-600 MHz tuning bands, and non-transmittable special channels.
