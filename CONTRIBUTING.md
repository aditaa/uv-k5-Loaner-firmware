# Contributing

Thanks for improving the loaner firmware. Keep each change focused, link it to
a GitHub issue, and work on a feature branch rather than `main`.

## Build and test

Docker is the canonical path because it pins the compiler, package snapshot,
Python dependencies, and formatting tools. From Git Bash, WSL, Linux, or
macOS:

```sh
VERSION_SUFFIX=LNR2415 ./compile-with-docker.sh
```

From Windows Command Prompt:

```bat
set VERSION_SUFFIX=LNR2415
compile-with-docker.bat
```

The full pipeline runs formatting, cppcheck, sanitizer-backed host tests, two
clean ARM builds, the firmware-size limit, packing, metadata verification, and
the reproducibility comparison. See [BUILDING.md](BUILDING.md) for native and
single-test commands.

## Pull requests

Use the pull-request template and include:

- the linked issue and user-visible/release impact;
- before/after/delta firmware size from a clean build;
- automated test results and any affected optional `ENABLE_*` builds;
- whether EEPROM or UART/CHIRP compatibility changed; and
- hardware steps and results, or a linked `hardware-required` issue naming the
  remaining test.

Do not report hardware-dependent work as complete based only on host tests.
RF, PA-disable, charging, USB electrical behavior, audio, and keypad changes
need the appropriate physical test evidence before release.

## Commits and review

Use short imperative commit subjects. Keep generated binaries and local build
output out of commits. `main` requires a pull request and all protected CI and
CodeQL checks; force pushes and branch deletion are disabled.

Before preparing a tag, follow the [release checklist](docs/release-checklist.md).

## Issue triage

Apply one priority and one area label when the scope is clear:

- `priority:p0`, `priority:p1`, or `priority:p2`;
- `area:firmware`, `area:radio-rf`, `area:ui`, `area:eeprom-chirp`,
  `area:power-usb`, or `area:build-ci`.

Add `hardware-required` when physical validation remains and
`release-blocking` only when the issue must be resolved before publishing the
next firmware release.
