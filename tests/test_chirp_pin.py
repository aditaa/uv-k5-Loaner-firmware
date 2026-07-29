import importlib.util
import json
from pathlib import Path

import pytest


def _load_module(name, path):
	spec = importlib.util.spec_from_file_location(name, Path(path))
	assert spec is not None
	assert spec.loader is not None
	module = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(module)
	return module


PIN = _load_module("chirp_pin", "ci/chirp_pin.py")


def test_committed_pin_is_immutable_upstream_chirp():
	pin = PIN.load_pin()

	assert pin["repository"] == "https://github.com/kk7ds/chirp.git"
	assert PIN.COMMIT_PATTERN.fullmatch(pin["commit"])
	assert pin["track_ref"] == "refs/heads/master"
	assert pin["upstream_context"] == "https://github.com/kk7ds/chirp/pull/1414"


def test_update_changes_only_commit(tmp_path):
	lock = tmp_path / "chirp.lock.json"
	original = PIN.load_pin()
	lock.write_text(json.dumps(original), encoding="utf-8")

	updated = PIN.update_commit(lock, "a" * 40)

	assert updated == {**original, "commit": "a" * 40}
	assert PIN.load_pin(lock) == updated


@pytest.mark.parametrize("commit", ["main", "A" * 40, "a" * 39])
def test_update_rejects_mutable_or_invalid_commit(tmp_path, commit):
	lock = tmp_path / "chirp.lock.json"
	lock.write_text(Path("ci/chirp.lock.json").read_text(encoding="utf-8"), encoding="utf-8")

	with pytest.raises(PIN.PinError, match="full 40-character"):
		PIN.update_commit(lock, commit)
