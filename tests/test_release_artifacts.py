import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest


def _load_module(name, path):
	spec = importlib.util.spec_from_file_location(name, Path(path))
	assert spec is not None
	assert spec.loader is not None
	module = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(module)
	return module


RELEASE = _load_module("release_artifacts", "ci/release_artifacts.py")
PACKER = _load_module("firmware_packer_for_release", "fw-pack.py")


@pytest.mark.parametrize(
	("tag", "suffix"),
	[
		("v24.03", "LNR2430"),
		("v24.10.5", "LNR24A5"),
		("v24.12.35", "LNR24CZ"),
	],
)
def test_tag_to_suffix(tag, suffix):
	assert RELEASE.tag_to_suffix(tag) == suffix


@pytest.mark.parametrize(
	"tag",
	["24.03", "v24.00", "v24.13", "v24.3", "v24.03.01", "v24.03.36", "v2024.03"],
)
def test_tag_to_suffix_rejects_invalid_tags(tag):
	with pytest.raises(RELEASE.ReleaseError):
		RELEASE.tag_to_suffix(tag)


def test_validate_tag_rejects_suffix_file_drift(tmp_path):
	suffix_file = tmp_path / "VERSION_SUFFIX"
	suffix_file.write_text("LNR2431\n", encoding="ascii")

	with pytest.raises(RELEASE.ReleaseError, match="expected LNR2430"):
		RELEASE.validate_tag("v24.03", suffix_file)


def test_release_bundle_records_and_verifies_integrity(tmp_path):
	raw_path = tmp_path / "firmware.bin"
	packed_path = tmp_path / "firmware.packed.bin"
	output_dir = tmp_path / "release"
	raw_path.write_bytes(b"\x5a" * 0x2200)
	packed_path.write_bytes(PACKER.pack_firmware(raw_path.read_bytes(), "LNR24A5"))

	manifest_path = RELEASE.bundle_artifacts(
		suffix="LNR24A5",
		raw_path=raw_path,
		packed_path=packed_path,
		output_dir=output_dir,
		source_commit="a" * 40,
		release_tag="v24.10.5",
	)
	RELEASE.verify_bundle(manifest_path, "LNR24A5", "v24.10.5")

	manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
	assert manifest["source_commit"] == "a" * 40
	assert manifest["build_environment"]["container_base"]
	assert manifest["build_environment"]["package_snapshot"]
	assert manifest["build_environment"]["source_date_epoch"]
	assert manifest["firmware_ids"]["uart_handshake"] == "1.02.LNR24A5"
	assert manifest["files"]["loaner-firmware-LNR24A5.bin"]["size"] == 0x2200
	assert (output_dir / "loaner-firmware-LNR24A5.sha256").is_file()


def test_release_bundle_detects_artifact_changes(tmp_path):
	raw_path = tmp_path / "firmware.bin"
	packed_path = tmp_path / "firmware.packed.bin"
	output_dir = tmp_path / "release"
	raw_path.write_bytes(b"\x5a" * 0x2200)
	packed_path.write_bytes(PACKER.pack_firmware(raw_path.read_bytes(), "LNR24A5"))
	manifest_path = RELEASE.bundle_artifacts(
		suffix="LNR24A5",
		raw_path=raw_path,
		packed_path=packed_path,
		output_dir=output_dir,
		source_commit="b" * 40,
		release_tag="v24.10.5",
	)
	(output_dir / "loaner-firmware-LNR24A5.bin").write_bytes(b"changed")

	with pytest.raises(RELEASE.ReleaseError, match="size mismatch"):
		RELEASE.verify_bundle(manifest_path, "LNR24A5", "v24.10.5")


def test_release_bundle_rejects_packed_image_from_different_raw_firmware(tmp_path):
	raw_path = tmp_path / "firmware.bin"
	packed_path = tmp_path / "firmware.packed.bin"
	raw_path.write_bytes(b"\x5a" * 0x2200)
	packed_path.write_bytes(PACKER.pack_firmware(b"\xa5" * 0x2200, "LNR24A5"))

	with pytest.raises(RELEASE.ReleaseError, match="does not match the raw firmware"):
		RELEASE.bundle_artifacts(
			suffix="LNR24A5",
			raw_path=raw_path,
			packed_path=packed_path,
			output_dir=tmp_path / "release",
			source_commit="c" * 40,
			release_tag="v24.10.5",
		)


def test_validate_tag_cli_writes_github_outputs(tmp_path):
	suffix_file = tmp_path / "VERSION_SUFFIX"
	github_output = tmp_path / "github-output"
	suffix_file.write_text("LNR24A5\n", encoding="ascii")

	result = subprocess.run(
		[
			sys.executable,
			"ci/release_artifacts.py",
			"validate-tag",
			"--tag",
			"v24.10.5",
			"--suffix-file",
			str(suffix_file),
			"--github-output",
			str(github_output),
		],
		check=True,
		capture_output=True,
		text=True,
	)

	assert result.stdout.strip() == "LNR24A5"
	assert github_output.read_text(encoding="utf-8") == (
		"version_suffix=LNR24A5\nartifact_stem=loaner-firmware-LNR24A5\n"
	)
