#!/usr/bin/env python3
"""Ensure pinned upstream CHIRP understands the built firmware and memory layout."""

import argparse
import builtins
import re
import sys
from pathlib import Path


SUFFIX_PATTERN = re.compile(r"^[A-Z0-9]{7}$")
FIRMWARE_ID_PATTERN = re.compile(rb"1\.02\.[A-Z0-9]{7}\x00")
DISPLAY_BANNER_PATTERN = re.compile(rb"OEFW-[A-Z0-9]{7}\x00")


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


def read_suffix(suffix_file: Path) -> str:
	try:
		suffix = suffix_file.read_text(encoding="ascii").strip()
	except OSError as error:
		raise RuntimeError(f"Unable to read firmware suffix from {suffix_file}: {error}") from error
	if not SUFFIX_PATTERN.fullmatch(suffix):
		raise RuntimeError("Firmware suffix must be exactly 7 uppercase alphanumeric characters")
	return suffix


def _extract_unique(raw: bytes, pattern: re.Pattern[bytes], label: str) -> str:
	matches = {match[:-1].decode("ascii") for match in pattern.findall(raw)}
	if len(matches) != 1:
		raise RuntimeError(
			f"Built firmware must contain exactly one unique {label}; found {sorted(matches)}"
		)
	return matches.pop()


def extract_firmware_ids(binary_path: Path, expected_suffix: str) -> tuple[str, str]:
	try:
		raw = binary_path.read_bytes()
	except OSError as error:
		raise RuntimeError(f"Unable to read built firmware {binary_path}: {error}") from error

	firmware_id = _extract_unique(raw, FIRMWARE_ID_PATTERN, "UART programming identifier")
	display_banner = _extract_unique(raw, DISPLAY_BANNER_PATTERN, "display banner")
	if firmware_id != f"1.02.{expected_suffix}":
		raise RuntimeError(
			f"Built UART identifier is {firmware_id}, expected 1.02.{expected_suffix}"
		)
	if display_banner != f"OEFW-{expected_suffix}":
		raise RuntimeError(
			f"Built display banner is {display_banner}, expected OEFW-{expected_suffix}"
		)
	return firmware_id, display_banner


def check_memory_bounds(misc_path: Path):
	data = misc_path.read_text(encoding="utf-8")

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


def exercise_driver(module, firmware_id):
	from chirp import bitwise, chirp_common, errors, memmap  # type: ignore

	class DummyPipe:
		def log(self, *args, **kwargs):
			pass

	raw = memmap.MemoryMapBytes(b"\x00" * getattr(module, "MEM_SIZE", 0x2000))
	radio = module.UVK5Radio(DummyPipe())
	radio.metadata = {"uvk5_firmware": firmware_id}
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


def build_parser() -> argparse.ArgumentParser:
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument("chirp_root", type=Path)
	parser.add_argument("firmware_binary", type=Path)
	parser.add_argument("--suffix-file", type=Path, default=Path("VERSION_SUFFIX"))
	return parser


def main(argv: list[str] | None = None) -> int:
	args = build_parser().parse_args(argv)
	try:
		suffix = read_suffix(args.suffix_file)
		firmware_id, display_banner = extract_firmware_ids(args.firmware_binary, suffix)
		module = load_uvk5_module(args.chirp_root.resolve())
		if not module.UVK5Radio.k5_approve_firmware(firmware_id):
			raise RuntimeError(f"CHIRP rejected built firmware identifier {firmware_id}")

		firmware_root = Path(__file__).resolve().parents[1]
		check_memory_bounds(firmware_root / "misc.h")
		exercise_driver(module, firmware_id)
		print(
			f"CHIRP accepts built identifier '{firmware_id}', display banner "
			f"'{display_banner}', and memory-layout mutations."
		)
		return 0
	except RuntimeError as error:
		print(f"check-chirp-compat: {error}", file=sys.stderr)
		return 1


if __name__ == "__main__":
	sys.exit(main())
