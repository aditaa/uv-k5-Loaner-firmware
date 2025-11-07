#!/usr/bin/env python3
"""Exercise the CHIRP UV-K5 driver against the current firmware layout."""

import os
import re
import sys
from pathlib import Path


def load_uvk5_module(chirp_root: Path):
    sys.path.insert(0, str(chirp_root))
    try:
        import chirp.drivers.uvk5 as uvk5  # type: ignore
    except ImportError as exc:
        raise RuntimeError(f"Unable to import chirp.drivers.uvk5: {exc}") from exc
    return uvk5


def check_memory_bounds(misc_path: Path):
    data = misc_path.read_text()

    def extract(name: str) -> int:
        match = re.search(rf"{name} = (\d+)U", data)
        if not match:
            raise RuntimeError(f"Unable to locate {name} in {misc_path}")
        return int(match.group(1))

    mr_last = extract("MR_CHANNEL_LAST")
    freq_first = extract("FREQ_CHANNEL_FIRST")
    last_channel = extract("LAST_CHANNEL") if "LAST_CHANNEL" in data else None

    if mr_last != 199:
        raise RuntimeError(
            f"Firmware MR channel bound is {mr_last}, expected 199."
        )

    if freq_first != 200:
        raise RuntimeError(
            f"Firmware VFO channel start is {freq_first}, expected 200."
        )

    if last_channel is not None and last_channel < 207:
        raise RuntimeError(
            f"Firmware LAST_CHANNEL is {last_channel}, expected at least 207."
        )


def synthesize_image(module) -> bytearray:
    size = getattr(module, "MEM_SIZE", 0x2000)
    return bytearray(size)


def exercise_driver(module):
    from chirp import chirp_common, errors, bitwise  # type: ignore

    raw = synthesize_image(module)

    radio = module.UVK5Radio()
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
    except errors.RadioError:
        pass

    baseline = raw[:]
    settings = radio.get_settings()
    mutations = {
        "ch1call": lambda rs: rs.value.set_value(5),
        "noaaautoscan": lambda rs: rs.value.set_value(True),
        "scan1en": lambda rs: rs.value.set_value("On"),
        "locktx": lambda rs: rs.value.set_value(True),
        "voxlevel": lambda rs: rs.value.set_value("5"),
        "key1short": lambda rs: rs.value.set_value("Alarm"),
    }
    for key, mut in mutations.items():
        setting = settings.get_setting(key)
        if setting is None:
            raise RuntimeError(f"Missing setting '{key}' in CHIRP driver")
        mut(setting)
    radio.set_settings(settings)

    for offset, name in [
        (0x0E70, "public_settings"),
        (0x0E78, "display_settings"),
        (0x0E90, "keypad_settings"),
        (0x0EA0, "voice_prompt"),
        (0x0F18, "scanlist"),
        (0x0F40, "lock_settings"),
    ]:
        if baseline[offset:offset + 8] == raw[offset:offset + 8]:
            raise RuntimeError(f"CHIRP settings change did not touch {name} block (0x{offset:04X})")

    temp_mem = radio.get_memory(2)
    temp_mem.empty = True
    radio.set_memory(temp_mem)
    if baseline == raw:
        raise RuntimeError("CHIRP memory operations did not modify the image; layout may have changed")


def main():
    if len(sys.argv) != 2:
        print("Usage: check-chirp-compat.py <path-to-chirp>", file=sys.stderr)
        sys.exit(1)

    chirp_root = Path(sys.argv[1]).resolve()
    module = load_uvk5_module(chirp_root)

    suffix = os.environ.get("COMPAT_SUFFIX", "LNR24.12.1")
    banner = f"OEFW-{suffix}"
    if not module.UVK5Radio.k5_approve_firmware(banner):
        raise RuntimeError(f"CHIRP rejected firmware banner {banner}")

    firmware_root = Path(__file__).resolve().parents[1]
    check_memory_bounds(firmware_root / "misc.h")
    exercise_driver(module)

    print(f"CHIRP accepts firmware banner '{banner}' and driver tests passed.")


if __name__ == "__main__":
    main()
