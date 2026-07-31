# Loaner Firmware v24.12.5 — LNR24C5

This release consolidates the firmware, compatibility, reliability, testing,
and release-process work merged since `v24.12.4`.

## Highlights

- Allow transmit throughout the firmware-supported 50–76 MHz and 108–600 MHz
  tuning ranges. Operators and programmers remain responsible for lawful and
  hardware-appropriate frequency, power, mode, and equipment use.
- Validate EEPROM settings and calibration data before use, and reject invalid
  UART command bounds instead of allowing malformed values into firmware
  state.
- Add bounded recovery for I2C, SPI, UART, display, flash, AES, and BK4819
  peripheral waits so a stalled device cannot trap the firmware forever.
- Pin and continuously test the compatible upstream CHIRP UV-K5 driver path,
  including the behavior discussed in
  [kk7ds/chirp#1414](https://github.com/kk7ds/chirp/pull/1414).
- Make ARM builds reproducible in a pinned container and publish verified raw,
  packed, manifest, and SHA-256 artifacts whose tag and embedded identifiers
  must agree.
- Add 114 sanitizer-backed host tests, deterministic formatting/static-analysis
  checks, structured contribution templates, protected-branch checks, and a
  documented software/hardware release gate.
- Remove unreachable main-screen key-dispatch leftovers while retaining UART,
  CHIRP, scanning, DTMF, voice prompts, and the boot-time maintenance menu.

## Compatibility and identifiers

- Display banner: `OEFW-LNR24C5`
- UART programming identifier: `1.02.LNR24C5`
- Packed metadata: `*OEFW-LNR24C5`
- Release tag: `v24.12.5`

## Expected release assets

- `loaner-firmware-LNR24C5.bin`
- `loaner-firmware-LNR24C5.packed.bin`
- `loaner-firmware-LNR24C5.manifest.json`
- `loaner-firmware-LNR24C5.sha256`

## Flashing

Flash the suffix-bearing packed image with the
[Egzumer UV Tools web flasher](https://egzumer.github.io/uvtools/). Select the
`loaner-firmware-LNR24C5.packed.bin` asset, put the radio into firmware download
mode, and choose **Flash firmware**. Do not use the raw `.bin` asset for normal
flashing.

## Hardware validation status

The release owner confirmed successful GMRS transmit on the final functional
firmware candidate, commit `1ed32cc` (`LNR24C5`, packed SHA-256
`8fc0672fdbb320332843fa865a7b34c34f1dc5f98b429a4c4f7b0884cac7b191`). The
release-tag commit adds documentation only; the firmware source and build
configuration are unchanged from that tested candidate.

The release owner explicitly deferred the following broader checks for this
release. They remain open follow-up work and are not represented as passing:

- #56 — complete radio hardware qualification;
- #37 — unlocked-band RF/transmit bench validation; and
- #46 — USB-C charging and charging-current diagnosis. The firmware audit found
  no charger-enable/control output, so physical charging failure remains a
  hardware-path investigation unless new evidence shows otherwise.
