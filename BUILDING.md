# Building the Loaner Firmware

This document walks through producing firmware binaries locally or inside the provided Docker wrapper. It mirrors the instructions that formerly lived in `README.md`.

## Prerequisites
- Docker (recommended path; covers the compiler, python tooling, lint, and tests).
- For native builds only: ARM GCC 10.3.1 toolchain on `PATH`, GNU Make, Python 3 with `crcmod`, plus optional `cppcheck` and `pytest`.

## Docker Build (recommended)
`./compile-with-docker.sh` produces the most reproducible binaries by packaging the entire toolchain and CI flow inside the container image.

1. From the repository root:
   ```sh
   VERSION_SUFFIX=LNR24.12.1 ./compile-with-docker.sh
   ```
2. The script builds the Docker image, runs `ci/run.sh` inside the container (cppcheck + pytest + firmware build), and drops artifacts to `compiled-firmware/` on your host:
   - `compiled-firmware/loaner-firmware.bin`
   - `compiled-firmware/loaner-firmware.packed.bin`

If the script fails, inspect the console output; lint or unit test failures abort the build so issues are caught before you publish a release.

## Native Build (optional)
Docker remains the preferred path. Only follow these steps if you must build locally with an existing toolchain:

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
   The build also exports `VERSION_SUFFIX` into the binaries. Set it explicitly (for example `make TARGET=loaner-firmware VERSION_SUFFIX=LNR24.12.1`) or create an `LNR*` git tag that the Makefile can discover. The build errors out if neither is present.

## Creating a Packed Binary Manually
If the packed image was not produced automatically (for example on a minimal native setup), run:
```sh
python3 fw-pack.py loaner-firmware.bin LNR24.12.1 loaner-firmware.packed.bin
```

- Replace `LNR24.12.1` with the same suffix you pass in via `VERSION_SUFFIX`. That value is embedded in both the welcome screen and the packed metadata.  
  Keep it under 10 ASCII characters (the script rejects longer strings).
- The packed image is required for PC loader flashing because it carries the metadata Quansheng's tool expects.

## Running Lint and Tests
- `./compile-with-docker.sh` already executes `ci/run.sh`, so every Docker build runs cppcheck, pytest, and the firmware build in one shot.
<<<<<<< HEAD
- GitHub Actions runs dedicated lint stages before building: a style job (`ruff` over the Python tooling and `shellcheck` over the scripts), a `clang-format` diff check on C/C++ changes, and a `cppcheck` pass on the firmware sources. Fix issues reported there before kicking off full builds. To run the format check locally, export the same diff and pipe it into `clang-format-diff -p1`.
=======
- GitHub Actions runs dedicated lint stages before building: a style job (`ruff` over the Python tooling and `shellcheck` over the scripts), a `clang-format` diff check on C/C++ changes, and a `cppcheck` pass on the firmware sources. Fix issues reported there before kicking off full builds. To run the format check locally, export the same diff and pipe it into `clang-format-diff -p1`.
>>>>>>> 633c3bb (Document branch workflow and local test commands)
- If you are working natively, `ci/run.sh` reproduces the same flow once the dependencies are installed (see the Dockerfile for the package list). Run it with the same suffix to mirror CI:
  ```sh
  VERSION_SUFFIX=LNR24.12.1 ./ci/run.sh
  ```
- GitHub Actions runs `pytest` under Python 3.10 and 3.12 before the Docker build; keep tests compatible with both versions.
- To run individual pieces, consult the script for the exact command switches, then invoke:
  ```sh
  cppcheck ...        # optional, mirrors the flags in ci/run.sh
  pytest              # runs tests/test_fw_pack.py
  make clean
  make TARGET=loaner-firmware
  ```
- Keep an eye on the binary size reported by `arm-none-eabi-size` at the end of the build when you toggle features.

## Feature Toggles
Feature flags live near the top of `Makefile` as `ENABLE_*` macros. The loaner build keeps the optional blocks (`AIRCOPY`, `ALARM`, `FMRADIO`, `NOAA`, `TX1750`, and the SRAM overlay) disabled by default to shrink the binary and hide extra menus. Adjust the macros if you need those features, then run `make clean` before comparing binary size after any toggle changes.

## Firmware Metadata and Releases
- A successful build leaves you with `firmware.bin` (raw) and, when Python and `crcmod` are available, `firmware.packed.bin`. The packed image is what Quansheng's loader validates.
- Use `fw-pack.py` to stamp a release tag into the packed image. `make` already invokes the script with `VERSION_SUFFIX`, so the packed file inherits the same banner. To repack manually, pass the suffix yourself (example above).
- When building outside of Docker, set `VERSION_SUFFIX` in your environment once (for example `export VERSION_SUFFIX=LNR24.12.1`) so every command picks up the same value.  
  For Docker builds, prefix the wrapper with the same variable:  
  ```sh
  VERSION_SUFFIX=LNR24.12.1 ./compile-with-docker.sh
  ```
- Change the `TARGET` on the `make` command line to tweak the output filenames without editing source, for example `make TARGET=loaner-firmware`.
- Before publishing a release, spot-check the welcome screen on hardware to make sure the tag matches what you intend to share with end users.
- Recommended version format: mirror other UV-K5 firmware projects (Quansheng's stock firmware ships as `v2.1.27`, Open Edition uses `OEFW-2023.09`). Tag milestones as `vYY.MM[.PATCH]` and feed a matching, <=10 character `VERSION_SUFFIX` (for example `LNR24.12.1`). CHIRP reads the full `*OEFW-LNR24.12.1` banner and treats it as a known build.

## Release Versioning Checklist
Follow this sequence for every tagged release:

0. **Create a release branch**: Start from `main` and branch before making release edits (for example `git checkout -b release/LNR24.12.1`). All commits should land via a merge request.
1. **Pick a suffix**: Choose a 10-character-or-shorter identifier in the form `LNRYY.MM[.PATCH]` (for example `LNR24.12.1`). The suffix should line up with the git tag you plan to publish (for example `v24.12.1`).
2. **Export the suffix** so every build step sees the same value:
   ```sh
   export VERSION_SUFFIX=LNR24.12.1
   ```
   (Or prefix individual commands with `VERSION_SUFFIX=...` if you prefer.)
3. **Build and test** (Docker path preferred):
   ```sh
   VERSION_SUFFIX=LNR24.12.1 ./compile-with-docker.sh
   ```
   This reproduces the CI pipeline (cppcheck + pytest + firmware build) and drops `compiled-firmware/loaner-firmware-LNR24.12.1.bin/.packed.bin`.  
   If you must build natively, run:
   ```sh
   make clean
   make TARGET=loaner-firmware VERSION_SUFFIX=LNR24.12.1
   pytest -q
   ```
<<<<<<< HEAD
   Either path should pass without warnings; capture the output for the merge request description. Confirm the printed firmware size stays below the configured limit (`MAX_FIRMWARE_SIZE`, default 122 880 bytes) so there is margin for future changes.
=======
   Either path should pass without warnings; capture the output for the merge request description. Confirm the printed firmware size stays below the configured limit (`MAX_FIRMWARE_SIZE`, default 122 880 bytes) so there is margin for future changes.
>>>>>>> 633c3bb (Document branch workflow and local test commands)
4. **Validate on hardware**: Flash the packed image and confirm the radio splash reports `OEFW-LNR24.12.1`.
5. **Tag the release** using the calendar semantic scheme:
   ```sh
   git tag -a v24.12 -m "Loaner firmware v24.12"
   git push origin v24.12
   ```
6. **Publish the GitHub release**: Attach the packed binary (`compiled-firmware/loaner-firmware-LNR24.12.1.packed.bin`) and include the validation steps in the notes. If you prefer CI-generated artifacts, trigger the `CI` workflow manually via “Run workflow” in GitHub and supply `LNR24.12.1` as the `version_suffix`; the workflow only uploads artifacts on manual runs.
7. **Upstream tooling**: When the suffix changes, update any dependent projects (for example CHIRP PR #1414) so they whitelist the new `OEFW-LNR` banner.

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
