## Loaner Firmware Alpha 4 – LNR24A4

- Force MR channels to render names (or the `CH-###` fallback) on the main screen so end users no longer see raw transmit frequencies.
- Default new boots to name display mode (`MDF_NAME`) regardless of prior EEPROM values, keeping radios aligned with the locked channel-only experience.

Artifacts generated via `./compile-with-docker.sh`:

- `compiled-firmware/loaner-firmware-LNR24A4.bin`
- `compiled-firmware/loaner-firmware-LNR24A4.packed.bin`
