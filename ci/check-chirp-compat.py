#!/usr/bin/env python3
import importlib.util
import os
import re
import sys
from pathlib import Path


def load_uvk5_module(chirp_root: Path):
    module_path = chirp_root / "chirp" / "drivers" / "uvk5.py"
    if not module_path.exists():
        raise FileNotFoundError(f"Cannot find uvk5.py at {module_path}")

    spec = importlib.util.spec_from_file_location("chirp.drivers.uvk5", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load chirp.drivers.uvk5 module")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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

    print(f"CHIRP accepts firmware banner '{banner}' and memory bounds look OK.")


if __name__ == "__main__":
    main()
