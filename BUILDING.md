# Building the Loaner Firmware

This document walks through producing firmware binaries locally or inside the provided Docker wrapper. It mirrors the instructions that formerly lived in `README.md`.

## Prerequisites
- Docker (recommended path; covers the compiler, python tooling, lint, and tests).
- For native builds only: ARM GCC 10.3.1 toolchain on `PATH`, GNU Make, Python 3 with `crcmod`, plus optional `cppcheck` and `pytest`.

## Docker Build (recommended)
`./compile-with-docker.sh` produces the most reproducible binaries by packaging the entire toolchain and CI flow inside the container image.

1. From the repository root:
   ```sh
   ./compile-with-docker.sh
   ```
2. The script builds the Docker image, runs `ci/run.sh` inside the container (cppcheck + pytest + firmware build), and drops artifacts to `compiled-firmware/` on your host:
   - `compiled-firmware/loaner-firmware.bin`
   - `compiled-firmware/loaner-firmware.packed.bin`

If the script fails, inspect the console output; lint or unit test failures abort the build so issues are caught before you publish a release.

## Native Build (optional)
When you already have the toolchain locally, you can mirror the Docker steps:

1. Clean previous objects:
   ```sh
   make clean
   ```
2. Build the firmware (the `TARGET` name controls the output filename):
   ```sh
   make TARGET=loaner-firmware
   ```
   The above command produces `loaner-firmware.bin`. If Python with `crcmod` is installed you will also get `loaner-firmware.packed.bin`.  
   If you omit `TARGET=...` the files are named `firmware.bin` / `firmware.packed.bin`.
   The build also exports `VERSION_SUFFIX` into the binaries. Set it explicitly (for example `make TARGET=loaner-firmware VERSION_SUFFIX=LNR24A5`) or create an `LNR*` git tag that the Makefile can discover. The build errors out if neither is present.

## Creating a Packed Binary Manually
If the packed image was not produced automatically (for example on a minimal native setup), run:
```sh
python3 fw-pack.py loaner-firmware.bin LNR24.03 loaner-firmware.packed.bin
```

- The second argument is the version tag embedded in both the welcome screen and the packed metadata (mirror the `VERSION_SUFFIX` you build with).  
  Keep it under 10 ASCII characters (the script rejects longer strings).
- The packed image is required for PC loader flashing because it carries the metadata Quansheng's tool expects.

## Running Lint and Tests
- `./compile-with-docker.sh` already executes `ci/run.sh`, so every Docker build runs cppcheck, pytest, and the firmware build in one shot.
- If you are working natively, `ci/run.sh` reproduces the same flow: it runs `cppcheck` with the project's suppressions, executes the Python unit tests, and builds the firmware with `TARGET=loaner-firmware`.
- To run individual pieces, consult the script for the exact command switches, then invoke:
  ```sh
  cppcheck ...        # optional, mirrors the flags in ci/run.sh
  pytest              # runs tests/test_fw_pack.py
  make clean
  make TARGET=loaner-firmware
  ```
- Keep an eye on the binary size reported by `arm-none-eabi-size` at the end of the build when you toggle features.

## Feature Toggles
Feature flags live near the top of `Makefile` as `ENABLE_*` macros. Adjust them to control optional modules, then rebuild. Run `make clean` before comparing binary size after any toggle changes.

## Firmware Metadata and Releases
- A successful build leaves you with `firmware.bin` (raw) and, when Python and `crcmod` are available, `firmware.packed.bin`. The packed image is what Quansheng's loader validates.
- Use `fw-pack.py` to stamp a release tag into the packed image. `make` already invokes the script with `VERSION_SUFFIX`, so the packed file inherits the same banner. To repack manually, pass the suffix yourself:
  ```sh
  python3 fw-pack.py firmware.bin "${VERSION_SUFFIX}" loaner-firmware.packed.bin
  ```
- When building outside of Docker, set `VERSION_SUFFIX` in your environment once (for example `export VERSION_SUFFIX=LNR24A5`) so every command picks up the same value.
- Change the `TARGET` on the `make` command line to tweak the output filenames without editing source, for example `make TARGET=loaner-firmware`.
- Before publishing a release, spot-check the welcome screen on hardware to make sure the tag matches what you intend to share with end users.
- Recommended version format: mirror other UV-K5 firmware projects (Quansheng's stock firmware ships as `v2.1.27`, Open Edition uses `OEFW-2023.09`). Tag milestones as `vYY.MM[.PATCH]` and feed a matching, <=10 character `VERSION_SUFFIX` (for example `LNR24.03`). CHIRP reads the full `*OEFW-LNR24.03` banner and treats it as a known build.

## Branching and Release Flow
1. Start work on a fresh branch instead of `main`:
   ```sh
   git checkout -b feature-name
   ```
2. Build and test (preferably with `./compile-with-docker.sh`), document the validation steps, then open a pull request back to `main`.
3. Once the branch merges, create an annotated tag for the milestone:
   ```sh
   git tag -a v0.3 -m "Loaner v0.3"
   git push origin v0.3
   ```
4. Draft a GitHub release from that tag and attach the packed firmware produced from the same commit (for example `compiled-firmware/loaner-firmware.packed.bin`).
5. Repeat the process for each milestone so end users always have a tagged firmware matching the published release notes.
