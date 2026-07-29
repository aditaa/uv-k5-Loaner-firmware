# Pinned build dependencies

Release builds use immutable or dated inputs so rebuilding the same commit and
firmware suffix can reproduce the same raw and packed images.

## Container

- Base: `archlinux:base-devel` for `linux/amd64`
- Manifest digest: `sha256:33c534be6c990710a878b37192904dd448e162ade06a201d95a80b42be2110c7`
- Arch package snapshot: `2026/07/28`
- Package list: `ci/container-packages.txt`

Update the image digest and repository date together. Build twice with the
same source commit and suffix before accepting the update. Both values and the
commit-derived `SOURCE_DATE_EPOCH` are recorded in each release manifest.

## Arm compiler

- Archive: `gcc-arm-none-eabi-10.3-2021.10-x86_64-linux.tar.bz2`
- SHA-256: `97dbb4f019ad1650b732faffcc881689cedc14e2b7ee863d390e0a41ef16c9a3`
- Official MD5 cross-check: `2383e4eb4ea23f248d33adc70dc3227e`

`ci/install-arm-toolchain.sh` verifies the committed SHA-256 before extracting
the archive. Update the URL, checksum file, and documented versions together.

## Python

GitHub Actions uses Python `3.10.18` and `3.12.11`. Direct and transitive test,
lint, and formatting packages are pinned in `ci/requirements-ci.txt`.

## CHIRP

Compatibility tests use the upstream `kk7ds/chirp` repository at the exact
commit recorded in `ci/chirp.lock.json`. CI builds the firmware with the root
`VERSION_SUFFIX`, extracts the UART programming identifier from the resulting
binary, and then exercises the pinned UV-K5 driver and EEPROM mutations.

The programming identifier remains `1.02.<VERSION_SUFFIX>` while the EEPROM
layout is compatible with the upstream UV-K5 driver. The human-facing display
banner remains `OEFW-<VERSION_SUFFIX>`. If the EEPROM layout diverges, introduce
a compatibility-major firmware identifier and a dedicated CHIRP subclass,
referencing https://github.com/kk7ds/chirp/pull/1414 for the upstream design
history.

The `Update CHIRP pin` workflow checks upstream `master` every Monday and can
also be run manually. When the tracked commit changes, it updates only the lock
file and opens a dependency PR so the normal compatibility tests and review are
required before the new commit becomes the release pin.

## GitHub Actions

Workflow `uses:` entries are pinned to full commit SHAs with the reviewed
release version in an inline comment. To update one, review the upstream
release notes, replace both the SHA and comment, run actionlint, and complete
the two-build firmware comparison.

| Action | Reviewed version | Commit |
| --- | --- | --- |
| `actions/checkout` | `v4.4.0` | `11d5960a326750d5838078e36cf38b85af677262` |
| `actions/setup-python` | `v5.6.0` | `a26af69be951a213d495a4c3e4e4022e16d87065` |
| `actions/upload-artifact` | `v4.6.2` | `ea165f8d65b6e75b540449e92b4886f43607fa02` |
| `github/codeql-action` | `v3.37.3` | `4187e74d05793876e9989daffde9c3e66b4acd07` |
