import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest


def _load_packer():
	spec = importlib.util.spec_from_file_location("firmware_packer", Path("fw-pack.py"))
	assert spec is not None
	assert spec.loader is not None
	module = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(module)
	return module


PACKER = _load_packer()


def run_fw_pack(*args, check=True):
	return subprocess.run(
		[sys.executable, "fw-pack.py", *map(str, args)],
		check=check,
		capture_output=True,
		text=True,
	)


def test_fw_pack_injects_version_and_verifies_image(tmp_path):
	plain = b"\x01\x02\x03\x04" * 4096
	input_bin = tmp_path / "input.bin"
	packed_bin = tmp_path / "output.bin"
	input_bin.write_bytes(plain)

	run_fw_pack("pack", input_bin, "LOANR01", packed_bin)
	result = run_fw_pack("verify", packed_bin, "LOANR01")

	data = packed_bin.read_bytes()
	assert len(data) == len(plain) + PACKER.METADATA_SIZE + 2
	assert PACKER.inspect_firmware(data) == "LOANR01"
	assert result.stdout.strip() == "LOANR01"


@pytest.mark.parametrize("suffix", ["short", "TOO-LNG", "lower01", "TOOLONG8"])
def test_fw_pack_rejects_invalid_suffixes(tmp_path, suffix):
	input_bin = tmp_path / "input.bin"
	packed_bin = tmp_path / "output.bin"
	input_bin.write_bytes(b"\x00" * 0x2100)

	result = run_fw_pack("pack", input_bin, suffix, packed_bin, check=False)

	assert result.returncode != 0
	assert "exactly 7 uppercase alphanumeric" in result.stderr
	assert not packed_bin.exists()


def test_fw_pack_rejects_small_input(tmp_path):
	input_bin = tmp_path / "input.bin"
	packed_bin = tmp_path / "output.bin"
	input_bin.write_bytes(b"\x00" * (PACKER.METADATA_OFFSET - 1))

	result = run_fw_pack("pack", input_bin, "LOANR01", packed_bin, check=False)

	assert result.returncode != 0
	assert "input firmware is too small" in result.stderr
	assert not packed_bin.exists()


def test_fw_pack_removes_stale_output_after_failure(tmp_path):
	input_bin = tmp_path / "input.bin"
	packed_bin = tmp_path / "output.bin"
	input_bin.write_bytes(b"too small")
	packed_bin.write_bytes(b"stale firmware")

	result = run_fw_pack("pack", input_bin, "LOANR01", packed_bin, check=False)

	assert result.returncode != 0
	assert not packed_bin.exists()


def test_fw_pack_rejects_corrupt_crc(tmp_path):
	packed_bin = tmp_path / "output.bin"
	packed = bytearray(PACKER.pack_firmware(b"\x00" * 0x2100, "LOANR01"))
	packed[100] ^= 0x01
	packed_bin.write_bytes(packed)

	result = run_fw_pack("verify", packed_bin, "LOANR01", check=False)

	assert result.returncode != 0
	assert "CRC mismatch" in result.stderr


def test_fw_pack_rejects_metadata_mismatch(tmp_path):
	packed_bin = tmp_path / "output.bin"
	packed_bin.write_bytes(PACKER.pack_firmware(b"\x00" * 0x2100, "LOANR01"))

	result = run_fw_pack("verify", packed_bin, "LOANR02", check=False)

	assert result.returncode != 0
	assert "suffix mismatch" in result.stderr


def test_fw_pack_requires_a_subcommand():
	result = run_fw_pack(check=False)

	assert result.returncode != 0
	assert "required" in result.stderr
