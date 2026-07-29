# Repository Guidelines

## Project Structure & Module Organization
- `app/` holds menu, scanner, and spectrum controllers; `driver/` wraps MCU peripherals; `bsp/` headers are generated from `hardware/*/*.def`.
- UI rendering lives in `ui/`; reusable helpers (battery, boot, power) sit under `helper/`; shared bitmaps and fonts remain in the repo root and `images/`.
- Third-party dependencies stay in `external/` (CMSIS, tiny printf); patch them upstream-first to reduce merge conflicts.
- Feature toggles and build-time limits are managed via the `ENABLE_*` blocks at the top of `Makefile`.

## Build, Test, and Development Commands
- `make` (or `win_make.bat`) builds both the raw and required packed firmware; a packing or metadata failure fails the build.
- `./compile-with-docker.sh` supplies a reproducible GCC 10.3.1 toolchain and writes artifacts to `compiled-firmware/`.
- `make clean` clears objects before benchmarking size; `make flash`/`make debug` expect OpenOCD with a J-Link config.
- `python3 fw-pack.py pack loaner-firmware.bin LNR24A5 loaner-firmware.packed.bin` injects metadata; use the `verify` subcommand before publishing an image.

## Coding Style & Naming Conventions
- Indent with tabs; macros remain uppercase snake-case (`ENABLE_*`, `SYSCON_*`).
- Use same-line opening braces for enums and structs, next-line opening braces for functions, and same-line braces for control statements. Declare pointers as `Type *name`, indent initializer elements by one tab, and column-align consecutive assignments.
- Follow existing naming: module globals use leading capitals (`gScreenLine`), static helpers stay lower_case, and files compile as C11.
- Order includes from local headers outward and wrap optional code in the matching `#ifdef ENABLE_*` guard.
- Treat `-Werror` seriously—run `make` locally to keep the build warning-free.

## Testing Guidelines
- Run `pytest -q`, the changed-line clang-format check, cppcheck, and an ARM build before opening a pull request.
- Perform smoke tests covering boot, menu navigation, audio, and any toggled `ENABLE_*` feature; log RF observations for signal work.
- Record the manual steps and outcomes in your pull request to help reviewers reproduce them.

## Commit & Pull Request Guidelines
- Follow the existing history with short, imperative subjects (`Fix typo`, `Add spectrum analyzer...`) and reference issues using `close #123` when relevant.
- Squash WIP commits before pushing; PR descriptions should call out touched modules, Makefile flags, and validation results.
- Attach screenshots, logs, or size diffs when behaviour or footprint changes, and list any artifacts (e.g., `loaner-firmware.packed.bin`) that reviewers should test.

## Branching & Release Workflow
- Create a feature branch for every change (`git checkout -b feature-name`) and never push commits straight to `main`.
- Open a pull request targeting `main` once the branch is ready; include build/test notes and hardware validation results.
- When a milestone lands, update `VERSION_SUFFIX`, merge it, and tag that exact commit using `vYY.MM[.PATCH]`; the release workflow rejects mismatched tags and existing releases.
- Keep release notes concise: highlight the loaner-facing changes and link the corresponding ICS-205 or CHIRP updates if applicable.

## Versioning Strategy
- Use `vYY.MM[.PATCH]` for git tags and releases. Automation maps the tag to the seven-character suffix `LNRYYMP`, using one base-36 digit for month and patch (for example `v24.10.5` maps to `LNR24A5`; an omitted patch maps to `0`). Patches above 35 are rejected.
- The packed firmware metadata must keep the `*OEFW-` prefix (Quansheng’s bootloader refuses anything else). For CHIRP compatibility we report the stock-style `1.02.<SUFFIX>` string over the UART handshake instead, while the welcome banner continues to show `OEFW-LNR2415`. Update the root `VERSION_SUFFIX` file whenever you change the suffix so CI/release builds stay consistent.
- Update the root `VERSION_SUFFIX` to the mapped value before tagging. Releases include suffix-bearing raw/packed binaries, a JSON build manifest, and SHA-256 checksums.

## Firmware Configuration Tips
- Adjust `ENABLE_*` groups in `Makefile` to keep only the features you can fit, and re-run `make clean` before remeasuring size.
- Introduce new toggles as `ENABLE_FEATURE_NAME`, update the surrounding comment block, and document user-facing switches in `README.md`.
