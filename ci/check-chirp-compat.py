#!/usr/bin/env python3
import importlib.util
import os
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

    print(f"CHIRP accepts firmware banner '{banner}'.")


if __name__ == "__main__":
    main()
