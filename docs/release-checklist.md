# Release checklist

## Software gate

- [ ] Every release-blocking issue is closed or explicitly deferred with a reason.
- [ ] `VERSION_SUFFIX` matches the planned `vYY.MM[.PATCH]` tag mapping.
- [ ] The canonical Docker pipeline passes from a clean checkout.
- [ ] CI, CodeQL, CHIRP compatibility, sanitizer tests, and reproducibility checks are green on the release commit.
- [ ] Raw and packed binaries, manifest, checksums, identifiers, and filenames agree.
- [ ] Firmware size is recorded and remains below the CI limit.
- [ ] Release notes cover user-visible behavior, compatibility, and known limitations.

## Hardware gate

- [ ] Boot, display, keypad/knob, speaker/audio, and normal receive are smoke-tested.
- [ ] Programming and read-back succeed with the pinned CHIRP-compatible path.
- [ ] PTT, PA disable, power levels, spurious output, and representative band edges pass the RF bench plan.
- [ ] USB-C charging/current behavior is verified on the intended hardware revisions and cable orientations.
- [ ] Any optional feature enabled for the release is exercised on hardware.
- [ ] Results and equipment details are recorded in the linked hardware issues.

## Publish

- [ ] Merge the release-preparation PR and tag that exact `main` commit.
- [ ] Confirm the automated GitHub release contains the verified four-file bundle.
- [ ] Download the published assets once and verify the manifest/checksums independently.
- [ ] Keep the release blocked if a required hardware result is missing or failed.
