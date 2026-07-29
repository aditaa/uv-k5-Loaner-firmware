#!/usr/bin/env python3
"""Validate and update the immutable CHIRP compatibility-test pin."""

import argparse
import json
import re
import sys
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LOCK_PATH = REPOSITORY_ROOT / "ci" / "chirp.lock.json"
COMMIT_PATTERN = re.compile(r"^[0-9a-f]{40}$")
REPOSITORY_PATTERN = re.compile(
	r"^https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\.git$"
)
REF_PATTERN = re.compile(r"^refs/(?:heads|tags)/[A-Za-z0-9._/-]+$")
CONTEXT_PATTERN = re.compile(
	r"^https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/(?:pull|issues)/[0-9]+$"
)
REQUIRED_FIELDS = {"commit", "repository", "track_ref", "upstream_context"}


class PinError(ValueError):
	pass


def validate_pin(pin: object) -> dict[str, str]:
	if not isinstance(pin, dict):
		raise PinError("CHIRP lock must contain a JSON object")
	if set(pin) != REQUIRED_FIELDS:
		missing = sorted(REQUIRED_FIELDS - set(pin))
		extra = sorted(set(pin) - REQUIRED_FIELDS)
		raise PinError(f"CHIRP lock fields differ (missing={missing}, extra={extra})")
	if not all(isinstance(value, str) for value in pin.values()):
		raise PinError("CHIRP lock values must be strings")

	validated = dict(pin)
	if not COMMIT_PATTERN.fullmatch(validated["commit"]):
		raise PinError("CHIRP commit must be a full 40-character lowercase SHA")
	if not REPOSITORY_PATTERN.fullmatch(validated["repository"]):
		raise PinError("CHIRP repository must be an HTTPS GitHub clone URL")
	if not REF_PATTERN.fullmatch(validated["track_ref"]):
		raise PinError("CHIRP tracking ref must be a full heads or tags ref")
	if ".." in validated["track_ref"] or "//" in validated["track_ref"]:
		raise PinError("CHIRP tracking ref contains an unsafe path component")
	if not CONTEXT_PATTERN.fullmatch(validated["upstream_context"]):
		raise PinError("CHIRP upstream context must be a GitHub issue or pull request URL")
	return validated


def load_pin(path: Path = DEFAULT_LOCK_PATH) -> dict[str, str]:
	try:
		pin = json.loads(path.read_text(encoding="utf-8"))
	except (OSError, json.JSONDecodeError) as error:
		raise PinError(f"unable to read CHIRP lock {path}: {error}") from error
	return validate_pin(pin)


def update_commit(path: Path, commit: str) -> dict[str, str]:
	pin = load_pin(path)
	if not COMMIT_PATTERN.fullmatch(commit):
		raise PinError("CHIRP commit must be a full 40-character lowercase SHA")
	pin["commit"] = commit
	path.write_text(json.dumps(pin, indent=2, sort_keys=True) + "\n", encoding="utf-8")
	return pin


def build_parser() -> argparse.ArgumentParser:
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument("--lock", type=Path, default=DEFAULT_LOCK_PATH)
	subparsers = parser.add_subparsers(dest="command", required=True)
	subparsers.add_parser("validate")
	get_parser = subparsers.add_parser("get")
	get_parser.add_argument("field", choices=sorted(REQUIRED_FIELDS))
	update_parser = subparsers.add_parser("update")
	update_parser.add_argument("commit")
	return parser


def main(argv: list[str] | None = None) -> int:
	args = build_parser().parse_args(argv)
	try:
		if args.command == "update":
			pin = update_commit(args.lock, args.commit)
			print(pin["commit"])
		else:
			pin = load_pin(args.lock)
			if args.command == "get":
				print(pin[args.field])
			else:
				print(pin["commit"])
		return 0
	except PinError as error:
		print(f"chirp-pin: {error}", file=sys.stderr)
		return 1


if __name__ == "__main__":
	sys.exit(main())
