# Building the Loaner Firmware

This document walks through producing firmware binaries locally or inside the provided Docker wrapper. It mirrors the instructions that formerly lived in `README.md`.

## Prerequisites
- ARM GCC 10.3.1 toolchain available on `PATH`.
- GNU Make.
- Python 3 with the `crcmod` module (only required for generating the packed image).
- Optional: Docker (for the reproducible build helper).

## Standard Build
1. From the repository root clean any prior objects so size measurements stay accurate:
   ```sh
   make clean
   ```
2. Build the firmware:
   ```sh
   make
   ```
   The default target emits `loaner-firmware.bin`. If Python with `crcmod` is installed you will also get `loaner-firmware.packed.bin`.

## Creating a Packed Binary Manually
If the packed image was not produced automatically, run:
```sh
python3 fw-pack.py loaner-firmware.bin AUTHOR VERSION loaner-firmware.packed.bin
```

- Choose a short author tag (defaults to `LOANER`) and a concise version string so the radio UI stays tidy.
- The packed image is preferred for PC loader flashing because it carries the metadata required by Quansheng’s tool.

## Reproducible Docker Build
The repo includes a helper that wraps the GCC 10.3.1 toolchain inside Docker:
```sh
./compile-with-docker.sh
```
Artifacts are written to `compiled-firmware/loaner-firmware*.bin`.

## Feature Toggles
Feature flags live near the top of `Makefile` as `ENABLE_*` macros. Adjust them to control optional modules, then rebuild. Run `make clean` before comparing binary size after any toggle changes.
