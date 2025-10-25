# UV-K5 Loaner Firmware

A stripped-down Quansheng UV-K5/K6 firmware build intended for radios that get passed around as loaners.  
This fork keeps the core reliability fixes from the community projects while removing advanced features that could let a borrower wander into settings you would rather keep locked down.

## Goals
- Keep radios in channel-only mode with predictable controls.
- Ship a clearly branded binary so volunteers know they are flashing the loaner image.
- Stay close to upstream bug fixes while documenting the custom pieces that matter for the loaner program.

> **Warning**  
> Flashing third-party firmware is always at your own risk. Test on non-critical hardware first and confirm RF behaviour before handing units out.

## Notable Differences From Full Builds
- VFO access is fully disabled (menu item removed, EEPROM flag forced off, side-key bindings cleared).
- Long-press actions that could restore VFO/MR mode are stripped.
- Menu layout retains only what is required for the channel-only workflow.
- Default key text, version strings, and build artifacts are renamed to highlight the loaner focus.

## Building
1. Install the ARM GCC 10.3.1 toolchain (or run the docker helper below).  
2. From the repo root run:
   ```sh
   make clean
   make
   ```
   The build emits `loaner-firmware.bin`; if Python with `crcmod` is available you will also get `loaner-firmware.packed.bin`.

### Reproducible Docker Build
```sh
./compile-with-docker.sh
```
Artifacts are written to `compiled-firmware/loaner-firmware*.bin`.

### Creating a Packed Binary Manually
If the build only produced the unpacked image, run:
```sh
python3 fw-pack.py loaner-firmware.bin AUTHOR VERSION loaner-firmware.packed.bin
```
Use a short author tag (defaults to `LOANER`) and a concise version label so the radio UI stays tidy.

## Flashing
- Prefer flashing `loaner-firmware.packed.bin` when using Quansheng’s PC loader.  
- OpenOCD users can run `make flash` (J-Link layout expected) once the toolchain and debugger are on PATH.

## Contributing
Open issues or PRs if you spot regressions that impact the loaner workflow.  
When adding optional features, gate them behind new `ENABLE_*` toggles so the default build stays minimal.

## Credits
Based on the open-source efforts by DualTachyon, OneOfEleven, Fagci, and the wider UV-K5 community. This fork simply repackages their work for the loaner-radio use case.

## License
Licensed under the Apache License 2.0. See `LICENSE` for details.
