import importlib.util
from pathlib import Path

import pytest


def _load_module(name, path):
	spec = importlib.util.spec_from_file_location(name, Path(path))
	assert spec is not None
	assert spec.loader is not None
	module = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(module)
	return module


COMPAT = _load_module("check_chirp_compat", "ci/check-chirp-compat.py")


def test_extracts_actual_firmware_ids_from_built_image(tmp_path):
	binary = tmp_path / "firmware.bin"
	binary.write_bytes(
		b"prefix\x00OEFW-LNR24A5\x00middle\x001.02.LNR24A5\x00suffix"
	)

	assert COMPAT.extract_firmware_ids(binary, "LNR24A5") == (
		"1.02.LNR24A5",
		"OEFW-LNR24A5",
	)


def test_rejects_firmware_id_from_a_different_build(tmp_path):
	binary = tmp_path / "firmware.bin"
	binary.write_bytes(b"OEFW-LNR24A4\x001.02.LNR24A4\x00")

	with pytest.raises(RuntimeError, match="expected 1.02.LNR24A5"):
		COMPAT.extract_firmware_ids(binary, "LNR24A5")


def test_rejects_missing_programming_identifier(tmp_path):
	binary = tmp_path / "firmware.bin"
	binary.write_bytes(b"OEFW-LNR24A5\x00")

	with pytest.raises(RuntimeError, match="UART programming identifier"):
		COMPAT.extract_firmware_ids(binary, "LNR24A5")
