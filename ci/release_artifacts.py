#!/usr/bin/env python3

import argparse
import hashlib
import importlib.util
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PACKER_PATH = REPOSITORY_ROOT / "fw-pack.py"
TAG_PATTERN = re.compile(
	r"^v(?P<year>[0-9]{2})\.(?P<month>0[1-9]|1[0-2])(?:\.(?P<patch>0|[1-9][0-9]?))?$"
)
SUFFIX_PATTERN = re.compile(r"^[A-Z0-9]{7}$")
BASE36 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
MANIFEST_SCHEMA = 1


class ReleaseError(ValueError):
	pass


def _load_packer():
	spec = importlib.util.spec_from_file_location("firmware_packer", PACKER_PATH)
	if spec is None or spec.loader is None:
		raise RuntimeError(f"unable to load firmware packer from {PACKER_PATH}")
	module = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(module)
	return module


def validate_suffix(suffix: str) -> str:
	if not SUFFIX_PATTERN.fullmatch(suffix):
		raise ReleaseError("VERSION_SUFFIX must be exactly 7 uppercase alphanumeric characters")
	return suffix


def tag_to_suffix(tag: str) -> str:
	match = TAG_PATTERN.fullmatch(tag)
	if match is None:
		raise ReleaseError("release tag must match vYY.MM or vYY.MM.PATCH")

	month = int(match.group("month"))
	patch = int(match.group("patch") or "0")
	if patch >= len(BASE36):
		raise ReleaseError("release patch must be between 0 and 35")
	return f"LNR{match.group('year')}{BASE36[month]}{BASE36[patch]}"


def file_sha256(path: Path) -> str:
	digest = hashlib.sha256()
	with path.open("rb") as handle:
		for chunk in iter(lambda: handle.read(1024 * 1024), b""):
			digest.update(chunk)
	return digest.hexdigest()


def first_version_line(command: list[str]) -> str:
	try:
		result = subprocess.run(command, check=True, capture_output=True, text=True)
	except (OSError, subprocess.CalledProcessError):
		return "unavailable"
	output = result.stdout or result.stderr
	return output.splitlines()[0].strip() if output else "unavailable"


def validate_tag(tag: str, suffix_file: Path) -> str:
	expected = tag_to_suffix(tag)
	try:
		actual = suffix_file.read_text(encoding="ascii").strip()
	except OSError as error:
		raise ReleaseError(f"unable to read suffix file {suffix_file}: {error}") from error
	validate_suffix(actual)
	if actual != expected:
		raise ReleaseError(
			f"VERSION_SUFFIX mismatch for {tag}: expected {expected}, found {actual}"
		)
	return actual


def bundle_artifacts(
	*,
	suffix: str,
	raw_path: Path,
	packed_path: Path,
	output_dir: Path,
	source_commit: str,
	release_tag: str | None,
) -> Path:
	validate_suffix(suffix)
	if not re.fullmatch(r"[0-9a-f]{40}", source_commit):
		raise ReleaseError("source commit must be a full 40-character lowercase SHA")
	if release_tag is not None and tag_to_suffix(release_tag) != suffix:
		raise ReleaseError(f"release tag {release_tag} does not map to suffix {suffix}")

	packer = _load_packer()
	raw_firmware = raw_path.read_bytes()
	packed_firmware = packed_path.read_bytes()
	packed_suffix = packer.inspect_firmware(packed_firmware)
	if packed_suffix != suffix:
		raise ReleaseError(
			f"packed firmware suffix mismatch: expected {suffix}, got {packed_suffix}"
		)
	if packer.pack_firmware(raw_firmware, suffix) != packed_firmware:
		raise ReleaseError("packed firmware does not match the raw firmware image")

	output_dir.mkdir(parents=True, exist_ok=True)
	stem = f"loaner-firmware-{suffix}"
	raw_output = output_dir / f"{stem}.bin"
	packed_output = output_dir / f"{stem}.packed.bin"
	manifest_path = output_dir / f"{stem}.manifest.json"
	checksums_path = output_dir / f"{stem}.sha256"
	shutil.copyfile(raw_path, raw_output)
	shutil.copyfile(packed_path, packed_output)

	files = {}
	for path, kind in ((raw_output, "raw"), (packed_output, "packed")):
		files[path.name] = {
			"kind": kind,
			"sha256": file_sha256(path),
			"size": path.stat().st_size,
		}

	manifest = {
		"schema": MANIFEST_SCHEMA,
		"release_tag": release_tag,
		"source_commit": source_commit,
		"build_environment": {
			"container_base": os.environ.get("BUILD_CONTAINER_BASE", "unavailable"),
			"package_snapshot": os.environ.get("BUILD_PACKAGE_SNAPSHOT", "unavailable"),
			"source_date_epoch": os.environ.get("SOURCE_DATE_EPOCH", "unavailable"),
		},
		"version_suffix": suffix,
		"firmware_ids": {
			"display_banner": f"OEFW-{suffix}",
			"packed_metadata": f"*OEFW-{suffix}",
			"uart_handshake": f"1.02.{suffix}",
		},
		"files": files,
		"tools": {
			"arm_gcc": first_version_line(["arm-none-eabi-gcc", "--version"]),
			"arm_ld": first_version_line(["arm-none-eabi-ld", "--version"]),
			"python": platform.python_version(),
			"packer": "fw-pack.py schema 1",
		},
	}
	manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

	checksum_paths = (raw_output, packed_output, manifest_path)
	checksums_path.write_text(
		"".join(f"{file_sha256(path)}  {path.name}\n" for path in checksum_paths),
		encoding="ascii",
	)
	return manifest_path


def verify_bundle(manifest_path: Path, expected_suffix: str, expected_tag: str | None) -> None:
	validate_suffix(expected_suffix)
	try:
		manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
	except (OSError, json.JSONDecodeError) as error:
		raise ReleaseError(f"unable to read manifest {manifest_path}: {error}") from error

	if manifest.get("schema") != MANIFEST_SCHEMA:
		raise ReleaseError("unsupported release manifest schema")
	if manifest.get("version_suffix") != expected_suffix:
		raise ReleaseError("release manifest suffix does not match the expected suffix")
	if manifest.get("release_tag") != expected_tag:
		raise ReleaseError("release manifest tag does not match the expected tag")
	if expected_tag is not None and tag_to_suffix(expected_tag) != expected_suffix:
		raise ReleaseError("expected release tag and suffix do not match")

	for filename, metadata in manifest.get("files", {}).items():
		path = manifest_path.parent / filename
		if not path.is_file():
			raise ReleaseError(f"release artifact is missing: {filename}")
		if path.stat().st_size != metadata.get("size"):
			raise ReleaseError(f"release artifact size mismatch: {filename}")
		if file_sha256(path) != metadata.get("sha256"):
			raise ReleaseError(f"release artifact checksum mismatch: {filename}")
		if metadata.get("kind") == "packed":
			packer = _load_packer()
			if packer.inspect_firmware(path.read_bytes()) != expected_suffix:
				raise ReleaseError(f"release artifact metadata mismatch: {filename}")

	checksums_path = manifest_path.with_suffix("").with_suffix(".sha256")
	if not checksums_path.is_file():
		raise ReleaseError(f"release checksum file is missing: {checksums_path.name}")
	checksum_paths = [manifest_path.parent / name for name in manifest["files"]]
	checksum_paths.append(manifest_path)
	expected_checksums = "".join(
		f"{file_sha256(path)}  {path.name}\n" for path in checksum_paths
	)
	if checksums_path.read_text(encoding="ascii") != expected_checksums:
		raise ReleaseError("release checksum file does not match the bundle")


def build_parser() -> argparse.ArgumentParser:
	parser = argparse.ArgumentParser(description="Validate release versions and firmware artifacts")
	subparsers = parser.add_subparsers(dest="command", required=True)

	suffix_parser = subparsers.add_parser("validate-suffix")
	suffix_parser.add_argument("suffix")

	tag_parser = subparsers.add_parser("tag-to-suffix")
	tag_parser.add_argument("tag")

	validate_parser = subparsers.add_parser("validate-tag")
	validate_parser.add_argument("--tag", required=True)
	validate_parser.add_argument("--suffix-file", required=True, type=Path)
	validate_parser.add_argument("--github-output", type=Path)

	bundle_parser = subparsers.add_parser("bundle")
	bundle_parser.add_argument("--suffix", required=True)
	bundle_parser.add_argument("--raw", required=True, type=Path)
	bundle_parser.add_argument("--packed", required=True, type=Path)
	bundle_parser.add_argument("--output-dir", required=True, type=Path)
	bundle_parser.add_argument("--source-commit", required=True)
	bundle_parser.add_argument("--tag")

	verify_parser = subparsers.add_parser("verify-bundle")
	verify_parser.add_argument("--manifest", required=True, type=Path)
	verify_parser.add_argument("--expected-suffix", required=True)
	verify_parser.add_argument("--expected-tag")
	return parser


def main(argv: list[str] | None = None) -> int:
	args = build_parser().parse_args(argv)
	try:
		if args.command == "validate-suffix":
			print(validate_suffix(args.suffix))
		elif args.command == "tag-to-suffix":
			print(tag_to_suffix(args.tag))
		elif args.command == "validate-tag":
			suffix = validate_tag(args.tag, args.suffix_file)
			print(suffix)
			if args.github_output is not None:
				with args.github_output.open("a", encoding="utf-8") as output:
					output.write(f"version_suffix={suffix}\n")
					output.write(f"artifact_stem=loaner-firmware-{suffix}\n")
		elif args.command == "bundle":
			manifest = bundle_artifacts(
				suffix=args.suffix,
				raw_path=args.raw,
				packed_path=args.packed,
				output_dir=args.output_dir,
				source_commit=args.source_commit,
				release_tag=args.tag,
			)
			print(manifest)
		else:
			verify_bundle(args.manifest, args.expected_suffix, args.expected_tag)
			print(f"verified {args.manifest}")
		return 0
	except (ReleaseError, OSError, ValueError) as error:
		print(f"release-artifacts: {error}", file=sys.stderr)
		return 1


if __name__ == "__main__":
	sys.exit(main())
