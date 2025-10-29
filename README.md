# UV-K5 Loaner Firmware
[![Build](https://github.com/aditaa/uv-k5-Loaner-firmware/actions/workflows/main.yml/badge.svg)](https://github.com/aditaa/uv-k5-Loaner-firmware/actions/workflows/main.yml)

A stripped-down Quansheng UV-K5/K6 firmware build intended for radios that get passed around as loaners.  
This fork keeps the core reliability fixes from the community projects while removing advanced features that could let a borrower wander into settings you would rather keep locked down.

> **Warning**  
> Flashing third-party firmware is always at your own risk. Test on non-critical hardware first and confirm RF behaviour before handing units out.

## Quickstart
1. Download the latest `loaner-firmware.packed.bin` from the project releases (or build it yourself—see `BUILDING.md`).
2. With the radio powered off, hold the **PTT** and the **top side key** while turning it on. The display should stay blank, indicating the bootloader is active.
3. Connect the USB cable, open Quansheng's PC programming tool, select *Firmware Update*, point it at the packed image, and start the transfer.
4. After the loader reports success, power the radio off and back on to confirm the loaner splash/version string.

## Firmware Versioning
- Update the root `VERSION` file before cutting a release; the build picks up that value automatically (fallbacks still work if a version is supplied on the `make` command line instead).
- `make` combines `AUTHOR_STRING` and the version token so the welcome screen and UART banner both show something like `LOANER 0.1.0`.
- `fw-pack.py` embeds the same 16-byte tag inside the packed image, letting web flashers verify the build metadata.

## Goals
- Keep radios in channel-only mode with predictable controls.
- Ship a clearly branded binary so volunteers know they are flashing the loaner image.
- Stay close to upstream bug fixes while documenting the custom pieces that matter for the loaner program.

## Notable Differences From Full Builds
- VFO access is fully disabled (menu item removed and EEPROM flag forced off).
- Long-press actions that could restore VFO/MR mode are stripped.
- Menu layout retains only what is required for the channel-only workflow.
- Default key text, version strings, and build artifacts are renamed to highlight the loaner focus.
- Number keys recall the first ten programmed MR channels directly; the legacy F+digit functions are disabled.
- Side buttons are fixed: the top selects VFO A, the bottom selects VFO B (short or long press).
- The physical menu key is disabled so borrowers cannot enter configuration screens.
- Main display always shows channel names instead of raw frequencies.

## Flashing
### Quansheng PC Loader (recommended)
1. Install Quansheng's UV-K5/K6 programming utility if it is not already on your workstation.
2. Copy `loaner-firmware.packed.bin` locally—the packed image carries the metadata the loader validates.
3. With the radio powered off, hold **PTT** + **top side key** and power it on to enter the firmware download mode (the screen remains blank).
4. Connect the USB cable (CH340 driver) and confirm the loader detects the serial port.
5. Choose *Firmware Update*, select the packed binary, and start the process. Do not disconnect power until the loader reports completion.
6. Power-cycle the radio and confirm the loaner splash/version text is displayed.

### J-Link / OpenOCD (`make flash`)
1. Install OpenOCD and ensure it is configured for a J-Link probe, matching the expectations baked into the repo's OpenOCD config.
2. Connect the debugger to the radio's programming header.
3. From the repository root run:
   ```sh
   make flash
   ```
4. Use `make debug` afterwards if you need an interactive OpenOCD session.

## Building From Source
Detailed build and packaging steps now live in `BUILDING.md`. Use that document when you need to regenerate or customize the binaries.

### Automated Checks
- `./compile-with-docker.sh` builds with the pinned toolchain and drops binaries under `compiled-firmware/`.
- `python3 ci/check_firmware.py` fails if code size grows past the loaner budget or if the branding banner changes unexpectedly.
- `python3 ci/test_chirp.py` confirms CHIRP compatibility. It verifies that the required `ENABLE_*` flags stay enabled, checks that CHIRP’s UV-K5 driver still whitelists the Loaner banner, and exercises the driver against the synthetic EEPROM image in `ci/synthetic_eeprom.bin` to ensure firmware options decode correctly.

## Contributing
Open issues or PRs if you spot regressions that impact the loaner workflow.  
When adding optional features, gate them behind new `ENABLE_*` toggles so the default build stays minimal.

## Project Backlog Snapshot
- `docs/issues/issue-export.json` captures the high-level loaner backlog for offline reference.
- `docs/issues/issues-detailed.json` preserves the matching GitHub issue metadata export.

## Credits
Based on the open-source efforts by DualTachyon, OneOfEleven, Fagci, and the wider UV-K5 community. This fork simply repackages their work for the loaner-radio use case.

## License
Licensed under the Apache License 2.0. See `LICENSE` for details.
Copyright 2023 Dual Tachyon
https://github.com/DualTachyon

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
