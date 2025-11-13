#!/usr/bin/env python3
"""Ensure CHIRP still understands this firmware layout."""

import os
import re
import sys
import builtins
from pathlib import Path


def load_uvk5_module(chirp_root: Path):
    sys.path.insert(0, str(chirp_root))
    install_gettext_fallback()
    try:
        import chirp.drivers.uvk5 as uvk5  # type: ignore
    except ImportError as exc:
        raise RuntimeError(f"Unable to import chirp.drivers.uvk5: {exc}") from exc
    return uvk5


def install_gettext_fallback():
    if getattr(builtins, "_", None):
        return

    def _identity(message, *args, **kwargs):
        return message

    builtins._ = _identity


def check_memory_bounds(misc_path: Path):
    data = misc_path.read_text()

    def extract(name: str) -> int:
        match = re.search(rf"{name} = (\d+)U", data)
        if not match:
            raise RuntimeError(f"Unable to locate {name} in {misc_path}")
        return int(match.group(1))

    mr_last = extract("MR_CHANNEL_LAST")
    freq_first = extract("FREQ_CHANNEL_FIRST")

    if mr_last != 199:
        raise RuntimeError(f"Firmware MR channel bound is {mr_last}, expected 199.")

    if freq_first != 200:
        raise RuntimeError(f"Firmware VFO channel start is {freq_first}, expected 200.")


def exercise_driver(module, banner):
    from chirp import chirp_common, errors, bitwise, memmap  # type: ignore

    class DummyPipe:
        def log(self, *args, **kwargs):
            pass

    raw = memmap.MemoryMapBytes(b"\x00" * getattr(module, "MEM_SIZE", 0x2000))
    radio = module.UVK5Radio(DummyPipe())
    radio.metadata = {"uvk5_firmware": banner}
    radio._mmap = raw
    radio._memobj = bitwise.parse(module.MEM_FORMAT, radio._mmap)

    mem = radio.get_memory(1)
    mem.name = "CI-CHECK"
    radio.set_memory(mem)

    failing = chirp_common.Memory()
    failing.number = 250
    failing.empty = False
    try:
        radio.set_memory(failing)
        raise RuntimeError("CHIRP accepted channel 250; memory bounds may be misaligned")
    except (errors.RadioError, IndexError):
        pass

    settings = radio.get_settings()
    for group in settings:
        for setting in group:
            try:
                _ = setting.value
            except Exception:
                continue

    baseline = raw.get_packed()
    temp_mem = radio.get_memory(2)
    temp_mem.empty = True
    radio.set_memory(temp_mem)
    if raw.get_packed() == baseline:
        raise RuntimeError("CHIRP memory operations did not modify the image; layout may have changed")


def main():
    if len(sys.argv) != 2:
        print("Usage: check-chirp-compat.py <path-to-chirp>", file=sys.stderr)
        sys.exit(1)

    chirp_root = Path(sys.argv[1]).resolve()
    module = load_uvk5_module(chirp_root)

    suffix = os.environ.get("COMPAT_SUFFIX", "LNR2415")
    firmware_id = f"1.02.{suffix}"
    if not module.UVK5Radio.k5_approve_firmware(firmware_id):
        raise RuntimeError(f"CHIRP rejected firmware identifier {firmware_id}")

    firmware_root = Path(__file__).resolve().parents[1]
    check_memory_bounds(firmware_root / "misc.h")
    exercise_driver(module, firmware_id)

    print(f"CHIRP accepts firmware identifier '{firmware_id}' and driver tests passed.")


if __name__ == "__main__":
    main()
