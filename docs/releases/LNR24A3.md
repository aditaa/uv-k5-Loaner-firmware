## Loaner Firmware Alpha 3 – LNR24A3

- Disable the physical Menu key so accidental presses no longer expose configuration menus.
- Clean build scripts to drop stale `loaner-firmware*.bin` artifacts before each Docker build, ensuring releases only contain fresh images.

Tag this build as `v24.10-alpha3` and publish the two artifacts below.

Artifacts generated via `./compile-with-docker.sh`:

- `compiled-firmware/loaner-firmware-LNR24A3.bin`
- `compiled-firmware/loaner-firmware-LNR24A3.packed.bin`
