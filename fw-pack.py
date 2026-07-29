#!/usr/bin/env python3

import argparse
import re
import sys
from binascii import crc_hqx
from itertools import cycle
from pathlib import Path


OBFUSCATION = [
	0x47, 0x22, 0xC0, 0x52, 0x5D, 0x57, 0x48, 0x94, 0xB1, 0x60, 0x60, 0xDB, 0x6F, 0xE3, 0x4C, 0x7C,
	0xD8, 0x4A, 0xD6, 0x8B, 0x30, 0xEC, 0x25, 0xE0, 0x4C, 0xD9, 0x00, 0x7F, 0xBF, 0xE3, 0x54, 0x05,
	0xE9, 0x3A, 0x97, 0x6B, 0xB0, 0x6E, 0x0C, 0xFB, 0xB1, 0x1A, 0xE2, 0xC9, 0xC1, 0x56, 0x47, 0xE9,
	0xBA, 0xF1, 0x42, 0xB6, 0x67, 0x5F, 0x0F, 0x96, 0xF7, 0xC9, 0x3C, 0x84, 0x1B, 0x26, 0xE1, 0x4E,
	0x3B, 0x6F, 0x66, 0xE6, 0xA0, 0x6A, 0xB0, 0xBF, 0xC6, 0xA5, 0x70, 0x3A, 0xBA, 0x18, 0x9E, 0x27,
	0x1A, 0x53, 0x5B, 0x71, 0xB1, 0x94, 0x1E, 0x18, 0xF2, 0xD6, 0x81, 0x02, 0x22, 0xFD, 0x5A, 0x28,
	0x91, 0xDB, 0xBA, 0x5D, 0x64, 0xC6, 0xFE, 0x86, 0x83, 0x9C, 0x50, 0x1C, 0x73, 0x03, 0x11, 0xD6,
	0xAF, 0x30, 0xF4, 0x2C, 0x77, 0xB2, 0x7D, 0xBB, 0x3F, 0x29, 0x28, 0x57, 0x22, 0xD6, 0x92, 0x8B,
]

METADATA_OFFSET = 0x2000
METADATA_PREFIX = b"*OEFW-"
METADATA_SIZE = 16
SUFFIX_PATTERN = re.compile(r"^[A-Z0-9]{7}$")


class FirmwarePackError(ValueError):
	pass


def obfuscate(firmware: bytes) -> bytes:
	return bytes(a ^ b for a, b in zip(firmware, cycle(OBFUSCATION)))


def validate_suffix(suffix: str) -> str:
	if not SUFFIX_PATTERN.fullmatch(suffix):
		raise FirmwarePackError("version suffix must be exactly 7 uppercase alphanumeric characters")
	return suffix


def version_block(suffix: str) -> bytes:
	validate_suffix(suffix)
	block = METADATA_PREFIX + suffix.encode("ascii")
	return block + (b"\x00" * (METADATA_SIZE - len(block)))


def crc_bytes(payload: bytes) -> bytes:
	crc = crc_hqx(payload, 0x0000)
	return bytes([crc & 0xFF, (crc >> 8) & 0xFF])


def pack_firmware(plain: bytes, suffix: str) -> bytes:
	if len(plain) < METADATA_OFFSET:
		raise FirmwarePackError(
			f"input firmware is too small: need at least {METADATA_OFFSET} bytes, got {len(plain)}"
		)

	clear = plain[:METADATA_OFFSET] + version_block(suffix) + plain[METADATA_OFFSET:]
	payload = obfuscate(clear)
	return payload + crc_bytes(payload)


def inspect_firmware(packed: bytes) -> str:
	minimum_size = METADATA_OFFSET + METADATA_SIZE + 2
	if len(packed) < minimum_size:
		raise FirmwarePackError(
			f"packed firmware is too small: need at least {minimum_size} bytes, got {len(packed)}"
		)

	payload, stored_crc = packed[:-2], packed[-2:]
	expected_crc = crc_bytes(payload)
	if stored_crc != expected_crc:
		raise FirmwarePackError(
			f"packed firmware CRC mismatch: expected {expected_crc.hex()}, got {stored_crc.hex()}"
		)

	clear = obfuscate(payload)
	block = clear[METADATA_OFFSET : METADATA_OFFSET + METADATA_SIZE]
	if not block.startswith(METADATA_PREFIX):
		raise FirmwarePackError("packed firmware metadata prefix is missing")

	suffix_bytes = block[len(METADATA_PREFIX) : len(METADATA_PREFIX) + 7]
	try:
		suffix = suffix_bytes.decode("ascii")
	except UnicodeDecodeError as error:
		raise FirmwarePackError("packed firmware suffix is not ASCII") from error
	validate_suffix(suffix)

	padding = block[len(METADATA_PREFIX) + 7 :]
	if padding != b"\x00" * len(padding):
		raise FirmwarePackError("packed firmware metadata padding is invalid")
	return suffix


def write_packed(input_path: Path, suffix: str, output_path: Path) -> None:
	if input_path.resolve() == output_path.resolve():
		raise FirmwarePackError("input and output paths must be different")
	temporary_path = output_path.with_name(f".{output_path.name}.tmp")
	try:
		packed = pack_firmware(input_path.read_bytes(), suffix)
		temporary_path.write_bytes(packed)
		temporary_path.replace(output_path)
	except Exception:
		if output_path.exists():
			output_path.unlink()
		raise
	finally:
		if temporary_path.exists():
			temporary_path.unlink()


def build_parser() -> argparse.ArgumentParser:
	parser = argparse.ArgumentParser(description="Pack and verify UV-K5 firmware images")
	subparsers = parser.add_subparsers(dest="command", required=True)

	pack_parser = subparsers.add_parser("pack", help="insert metadata and pack a raw firmware image")
	pack_parser.add_argument("input", type=Path)
	pack_parser.add_argument("suffix")
	pack_parser.add_argument("output", type=Path)

	verify_parser = subparsers.add_parser("verify", help="verify CRC and embedded metadata")
	verify_parser.add_argument("input", type=Path)
	verify_parser.add_argument("suffix", nargs="?")
	return parser


def main(argv: list[str] | None = None) -> int:
	args = build_parser().parse_args(argv)
	try:
		if args.command == "pack":
			write_packed(args.input, args.suffix, args.output)
			return 0

		suffix = inspect_firmware(args.input.read_bytes())
		if args.suffix is not None and suffix != validate_suffix(args.suffix):
			raise FirmwarePackError(
				f"packed firmware suffix mismatch: expected {args.suffix}, got {suffix}"
			)
		print(suffix)
		return 0
	except (FirmwarePackError, OSError) as error:
		print(f"fw-pack: {error}", file=sys.stderr)
		return 1


if __name__ == "__main__":
	sys.exit(main())
