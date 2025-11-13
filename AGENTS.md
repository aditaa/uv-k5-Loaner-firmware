# Repository Guidelines

## Project Structure & Module Organization
- `app/` holds menu, scanner, and spectrum controllers; `driver/` wraps MCU peripherals; `bsp/` headers are generated from `hardware/*/*.def`.
- UI rendering lives in `ui/`; reusable helpers (battery, boot, power) sit under `helper/`; shared bitmaps and fonts remain in the repo root and `images/`.
- Third-party dependencies stay in `external/` (CMSIS, tiny printf); patch them upstream-first to reduce merge conflicts.
- Feature toggles and build-time limits are managed via the `ENABLE_*` blocks at the top of `Makefile`.

## Build, Test, and Development Commands
- `make` (or `win_make.bat`) builds `loaner-firmware.bin`; when Python + `crcmod` is available it also emits `loaner-firmware.packed.bin`.
- `./compile-with-docker.sh` supplies a reproducible GCC 10.3.1 toolchain and writes artifacts to `compiled-firmware/`.
- `make clean` clears objects before benchmarking size; `make flash`/`make debug` expect OpenOCD with a J-Link config.
- `python3 fw-pack.py loaner-firmware.bin AUTHOR VERSION loaner-firmware.packed.bin` injects metadata so web flashers accept the build.

## Coding Style & Naming Conventions
- Indent with tabs and place braces on the following line (Allman style); macros remain uppercase snake-case (`ENABLE_*`, `SYSCON_*`).
- Follow existing naming: module globals use leading capitals (`gScreenLine`), static helpers stay lower_case, and files compile as C2x.
- Order includes from local headers outward and wrap optional code in the matching `#ifdef ENABLE_*` guard.
- Treat `-Werror` seriously—run `make` locally to keep the build warning-free.

## Testing Guidelines
- No automated suite ships here; always compile locally and validate the affected features on hardware.
- Perform smoke tests covering boot, menu navigation, audio, and any toggled `ENABLE_*` feature; log RF observations for signal work.
- Record the manual steps and outcomes in your pull request to help reviewers reproduce them.

## Commit & Pull Request Guidelines
- Follow the existing history with short, imperative subjects (`Fix typo`, `Add spectrum analyzer...`) and reference issues using `close #123` when relevant.
- Squash WIP commits before pushing; PR descriptions should call out touched modules, Makefile flags, and validation results.
- Attach screenshots, logs, or size diffs when behaviour or footprint changes, and list any artifacts (e.g., `loaner-firmware.packed.bin`) that reviewers should test.

## Branching & Release Workflow
- Create a feature branch for every change (`git checkout -b feature-name`) and never push commits straight to `main`.
- Open a pull request targeting `main` once the branch is ready; include build/test notes and hardware validation results.
- When a milestone lands, tag the merge commit (for example `git tag -a v0.3`) and cut a GitHub release that attaches the packed firmware built from that tag.
- Keep release notes concise: highlight the loaner-facing changes and link the corresponding ICS-205 or CHIRP updates if applicable.

## Versioning Strategy
- Follow the calendar-semver pattern used by other UV-K5 forks (e.g. Quansheng's `v2.1.27` and Open Edition's `OEFW-2023.09`). Adopt `vYY.MM[.PATCH]` for git tags and releases (for example `v24.03` or `v24.03.1` for hotfixes).
- The packed firmware metadata must keep the `*OEFW-` prefix (Quansheng’s bootloader refuses anything else). For CHIRP compatibility we report the stock-style `1.02.<SUFFIX>` string over the UART handshake instead, while the welcome banner continues to show `OEFW-LNR2414`.
- Update the tag, the packed image suffix, and the GitHub release name together so end users and CHIRP all report the same version string.

## Firmware Configuration Tips
- Adjust `ENABLE_*` groups in `Makefile` to keep only the features you can fit, and re-run `make clean` before remeasuring size.
- Introduce new toggles as `ENABLE_FEATURE_NAME`, update the surrounding comment block, and document user-facing switches in `README.md`.
