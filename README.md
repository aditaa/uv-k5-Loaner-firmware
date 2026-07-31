# UV-K5 Loaner Firmware
[![Build](https://github.com/aditaa/uv-k5-Loaner-firmware/actions/workflows/main.yaml/badge.svg)](https://github.com/aditaa/uv-k5-Loaner-firmware/actions/workflows/main.yaml)

A stripped-down Quansheng UV-K5/K6 firmware build intended for radios that get passed around as loaners. This fork keeps the community reliability fixes while removing configuration rabbit holes so a first-time user can turn the knob, press PTT, and get on the air.

The project also gives COML/COMT staff a predictable path from the ICS-205 form to a radio codeplug: program the memories in CHIRP, flash the loaner binary, and the handset stays aligned with the paperwork.

> **Warning**  
> Flashing third-party firmware is always at your own risk. Test on non-critical hardware first and confirm RF behaviour before handing units out.

## Quickstart
1. Download the latest suffix-bearing packed release (for example `loaner-firmware-LNR24C5.packed.bin`) from the Releases page and, when practical, compare it with the published SHA-256 file.
2. Open the [Egzumer UV Tools web flasher](https://egzumer.github.io/uvtools/) in a browser that supports serial-device access, then choose **Select firmware file** and select the packed image.
3. With the radio powered off, hold the **PTT** and the **top side key** while turning it on. The display should stay blank, indicating the bootloader is active.
4. Connect the USB programming cable, choose **Flash firmware**, select the radio's serial port if prompted, and do not disconnect power or the cable until the transfer completes.
5. Power the radio off and back on to confirm the welcome screen shows the release tag from the packed image.
6. Spin the channel knob and verify that the loaner channel names appear as expected.

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
- Unlocked transmit policy: regional lock presets do not restrict programmed memories. The firmware permits transmit throughout its defined 50–76 MHz and 108–600 MHz tuning bands; the person programming and operating each radio is responsible for choosing authorized frequencies, modes, power levels, and equipment.

## Programming Channel Plans With CHIRP

This build assumes the channel plan lives on your ICS-205. To move that plan into a radio:

1. Prepare the ICS-205 so each channel has a concise label (CHIRP shows up to seven characters by default).
2. Launch CHIRP, connect the radio, and use `Radio -> Download From Radio` once to confirm the driver handshake.
3. Use `File -> Import` to pull in either a CSV exported from your ICS-205 or an existing `.img` template. Map the columns to CHIRP's `Name`, `Frequency`, `Tone Mode`, and `Tone` fields.
4. Sort the memories into the order that matches your loaner numbering, then `File -> Save As` to keep the template for the next deployment.
5. Upload the plan with `Radio -> Upload To Radio`. After the radio reboots, rotate the channel knob and verify that the display shows the ICS-205 names.
6. Repeat for each handset; the standard workflow keeps the handset in channel mode, so operators only see the memories you defined.

### Detailed upstream CHIRP workflow

The radio reports `1.02.<VERSION_SUFFIX>` to programming software, which identifies its EEPROM layout as compatible with the upstream UV-K5 driver. The separate `OEFW-<VERSION_SUFFIX>` display banner gives field users the recognizable loaner label without changing CHIRP's compatibility contract.

1. Install a current CHIRP daily build from the upstream CHIRP project.
2. Plug in the CH340 cable, switch the radio **on** in normal operating mode, and note the serial port name (`/dev/ttyUSB0`, `COM3`, etc.).
3. In CHIRP choose `Radio -> Download From Radio`, set **Vendor** to `Quansheng` and **Model** to `UV-K5`, then select the serial port.
4. Once the download succeeds, edit memories as usual. Keep the channel plan within memories 1 through 200.
5. Upload with `Radio -> Upload To Radio` using the same model selection. After the radio restarts, verify the channel names against the ICS-205.

If CHIRP reports an unsupported firmware version, first confirm that the regular **Quansheng -> UV-K5** driver is selected and that the radio is running an official release artifact. Each release manifest records the exact upstream CHIRP commit tested by CI.

The current firmware intentionally keeps the OEM-compatible EEPROM layout. If that layout ever changes, the firmware identifier must gain a compatibility-major version and CHIRP must gain a dedicated subclass; the design history is recorded in [kk7ds/chirp#1414](https://github.com/kk7ds/chirp/pull/1414).

Tip: Keep a CHIRP image with the baseline loaner plan in source control so teams can diff changes before distributing updates. After each upload, rotate the knob and confirm the ICS-205 names match the paperwork.

## Flashing

Use only the [Egzumer UV Tools web flasher](https://egzumer.github.io/uvtools/) for release images:

1. Download the suffix-bearing `*.packed.bin` file from the GitHub release. Do not use the raw `*.bin` file for normal flashing.
2. Open UV Tools in a browser that supports serial-device access and choose **Select firmware file**.
3. Select the downloaded packed image.
4. With the radio powered off, hold **PTT** + **top side key** and power it on. The blank screen indicates firmware download mode.
5. Connect the USB programming cable and choose **Flash firmware**. Select the radio's serial port if the browser asks for permission.
6. Leave the radio powered and connected until the transfer completes, then power-cycle it and confirm the loaner splash/version text.

## Field Notes
- Carry one handset that stayed stock as a control; it helps confirm the loader steps when training new volunteers.
- Log which firmware release you flashed (the welcome banner shows the tag) alongside the ICS-205 so future updates are easy to track.
- If a user reports odd audio or RF behaviour, record the firmware suffix and reproduction steps, then power-cycle and reseat the battery before deeper diagnosis.

## Need to Modify the Firmware?
All developer-facing build and packaging details live in `BUILDING.md`. Start there if you need to regenerate binaries or adjust feature toggles.

## Contributing
Open issues or PRs if you spot regressions that impact the loaner workflow. See [CONTRIBUTING.md](CONTRIBUTING.md) for the canonical build, validation, firmware-size, CHIRP, and hardware-test requirements.

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
