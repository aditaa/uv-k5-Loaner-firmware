#!/usr/bin/env python3
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
    last_channel = extract("LAST_CHANNEL")

    if mr_last != 199:
        raise RuntimeError(
            f"Firmware MR channel bound is {mr_last}, expected 199. "
            "Updating this constant will desynchronise CHIRP's memory map."
        )

    if freq_first != 200:
        raise RuntimeError(
            f"Firmware VFO channel start is {freq_first}, expected 200."
        )

    if last_channel < 207:
        raise RuntimeError(
            f"Firmware LAST_CHANNEL is {last_channel}, expected at least 207."
        )


def main():
    if len(sys.argv) != 2:
        print("Usage: check-chirp-compat.py <path-to-chirp>", file=sys.stderr)
        sys.exit(1)

    chirp_root = Path(sys.argv[1]).resolve()
    suffix = os.environ.get("COMPAT_SUFFIX", "LNR24.12.1")
    banner = f"OEFW-{suffix}"

    module = load_uvk5_module(chirp_root)

    if not hasattr(module, "UVK5Radio"):
        raise RuntimeError("chirp.drivers.uvk5 does not expose UVK5Radio")

    if not module.UVK5Radio.k5_approve_firmware(banner):
        print(
            f"chirp.drivers.uvk5 rejected firmware banner '{banner}'. "
            "Update the CHIRP whitelist or adjust the suffix.",
            file=sys.stderr,
        )
        sys.exit(1)

    firmware_root = Path(__file__).resolve().parents[1]
    check_memory_bounds(firmware_root / "misc.h")
    exercise_driver(module, chirp_root)

    print(f"CHIRP accepts firmware banner '{banner}' and driver tests passed.")


if __name__ == "__main__":
    main()
def exercise_driver(module, chirp_root: Path):
    from chirp import chirp_common, errors, bitwise  # type: ignore

    image_paths = [
        chirp_root / "tests" / "images" / "uvk5.img",
        chirp_root / "tests" / "images" / "UV-K5.img",
    ]
    image_path = next((p for p in image_paths if p.exists()), None)
    if image_path is None:
        raise FileNotFoundError("Unable to locate a sample UV-K5 image under tests/images")

    raw = bytearray(image_path.read_bytes())

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

    settings = radio.get_settings()
    mutations = {
        "ch1call": lambda rs: rs.value.set_value(5),
        "noaaautoscan": lambda rs: rs.value.set_value(True),
        "scan1en": lambda rs: rs.value.set_value("On"),
        "locktx": lambda rs: rs.value.set_value(True),
    }

    for key, mut in mutations.items():
        rs = settings.get_setting(key)
        if rs is None:
            raise RuntimeError(f"Missing setting '{key}' in CHIRP driver")
        mut(rs)

    radio.set_settings(settings)
