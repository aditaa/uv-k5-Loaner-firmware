# UV-K5 Loaner Firmware
[![Build](https://github.com/aditaa/uv-k5-Loaner-firmware/actions/workflows/main.yaml/badge.svg)](https://github.com/aditaa/uv-k5-Loaner-firmware/actions/workflows/main.yaml)

A stripped-down Quansheng UV-K5/K6 firmware build intended for radios that get passed around as loaners. This fork keeps the community reliability fixes while removing configuration rabbit holes so a first-time user can turn the knob, press PTT, and get on the air.

The project also gives COML/COMT staff a predictable path from the ICS-205 form to a radio codeplug: program the memories in CHIRP, flash the loaner binary, and the handset stays aligned with the paperwork.

> **Warning**  
> Flashing third-party firmware is always at your own risk. Test on non-critical hardware first and confirm RF behaviour before handing units out.

## Quickstart
1. Download the latest packed release (`loaner-firmware.packed.bin`) from the Releases page.
2. With the radio powered off, hold the **PTT** and the **top side key** while turning it on. The display should stay blank, indicating the bootloader is active.
3. Connect the USB cable, open Quansheng's PC programming tool, select *Firmware Update*, point it at the packed image, and start the transfer.
4. After the loader reports success, power the radio off and back on to confirm the welcome screen shows the release tag from the packed image.
5. Spin the channel knob and verify that the loaner channel names appear as expected.

## Design Goals
- Put channel-only handsets in the hands of volunteers who have minimal or no radio training.
- Give COML/COMT staff an efficient way to push an ICS-205 channel plan onto the radios using CHIRP.
- Track upstream bug fixes while documenting the toggles that keep the loaner build focused and predictable.

## Loaner Feature Highlights
- Channel knob only: the firmware boots into MR mode and ignores attempts to switch into VFO.
- Hardened menu: configuration items that could drift from the loaner plan are removed or disabled.
- Friendly prompts: welcome banner, battery indicator, and RSSI display identify the handset as a loaner and keep checks simple.
- Consistent keypad: digits recall the first ten memories, side buttons select the active VFO, and Menu is locked out.
- Lean feature set: Aircopy, FM broadcast, NOAA weather, the 1750 Hz tone burst, and the general alarm are compiled out so the UI stays focused on assigned channels and the binary remains compact.

## Programming Channel Plans With CHIRP
This build assumes the channel plan lives on your ICS-205. To move that plan into a radio:

1. Prepare the ICS-205 so each channel has a concise label (CHIRP shows up to seven characters by default).
2. Launch CHIRP, connect the radio, and use `Radio -> Download From Radio` once to confirm the driver handshake.
3. Use `File -> Import` to pull in either a CSV exported from your ICS-205 or an existing `.img` template. Map the columns to CHIRP's `Name`, `Frequency`, `Tone Mode`, and `Tone` fields.
4. Sort the memories into the order that matches your loaner numbering, then `File -> Save As` to keep the template for the next deployment.
5. Upload the plan with `Radio -> Upload To Radio`. After the radio reboots, rotate the channel knob and verify that the display shows the ICS-205 names.
6. Repeat for each handset; the standard workflow keeps the handset in channel mode, so operators only see the memories you defined.

### Detailed CHIRP workflow (UV-K5 + Egzumer/OSFW build)

The loaner firmware reports the stock handshake string (`1.02.LNR2415`), so you can stay on the upstream CHIRP tree. Use the existing **Quansheng → UV-K5 (Plus / unsupported / OSFW)** driver entry that Egzumer added for the Plus/OSFW firmware:

1. Update to the latest CHIRP daily build (or the Egzumer fork) so that “UV-K5 (Plus / unsupported / OSFW)” shows up under `Radio → Download From Radio`.
2. Plug in the CH340 cable, switch the radio **on** (normal operation), and note the serial port name (`/dev/ttyUSB0`, `COM3`, etc.).
3. In CHIRP choose `Radio → Download From Radio`, set **Vendor** to `Quansheng` and **Model** to `UV-K5 (Plus / unsupported / OSFW)`, then pick the serial port. Leave the radio unlocked; the loaner build keeps the keypad constrained but still answers the driver handshake.
4. Once the download succeeds, edit memories as usual. Because the firmware only exposes 200 MR channels, keep your plan within that range.
5. Upload with `Radio → Upload To Radio` using the same model selection. CHIRP will send the `1.02.LNR2415` identifier, which the radio accepts; the on-radio splash still says `OEFW-LNR2415` so field users see the loaner tag.

If CHIRP warns that it cannot recognise the firmware, double-check that you selected the “Plus / unsupported / OSFW” entry—selecting the vanilla UV-K5 or K5 Plus targets will fail the version check.

Tip: Keep a CHIRP image with the baseline loaner plan in source control so teams can diff changes before distributing updates. After each upload, rotate the knob and confirm the ICS-205 names match the paperwork.

Tip: Keep a CHIRP image with the baseline loaner plan in source control so teams can diff changes before distributing updates.

## Flashing
### Quansheng PC Loader (recommended)
1. Install Quansheng's UV-K5/K6 programming utility if it is not already on your workstation.
2. Copy the packed binary locally - the metadata is required by Quansheng's loader.
3. With the radio powered off, hold **PTT** + **top side key** and power it on to enter firmware download mode (the screen remains blank).
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

## Field Notes
- Carry one handset that stayed stock as a control; it helps confirm the loader steps when training new volunteers.
- Log which firmware release you flashed (the welcome banner shows the tag) alongside the ICS-205 so future updates are easy to track.
- If a user reports odd audio or RF behaviour, power cycle and reseat the battery first; the firmware keeps settings read-only so faults are usually hardware.

## Need to Modify the Firmware?
All developer-facing build and packaging details live in `BUILDING.md`. Start there if you need to regenerate binaries or adjust feature toggles.

## Contributing
Open issues or PRs if you spot regressions that impact the loaner workflow. Documentation updates (especially CHIRP workflows and loaner field notes) are welcome.

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
