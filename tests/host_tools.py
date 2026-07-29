import os
import shutil
import subprocess
import sys
from collections.abc import Iterable
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def host_compiler() -> str:
	requested = os.environ.get("CC")
	candidates = [requested] if requested else ["cc", "gcc", "clang"]
	for candidate in candidates:
		if candidate and (compiler := shutil.which(candidate)):
			return compiler

	message = "A host C compiler is required for firmware host tests"
	if os.environ.get("HOST_TESTS_REQUIRED") == "1":
		pytest.fail(message)
	pytest.skip(message)


def sanitizer_flags(*, shared: bool) -> list[str]:
	if sys.platform == "win32":
		return []

	requested = [
		name.strip()
		for name in os.environ.get("HOST_SANITIZERS", "").split(",")
		if name.strip()
	]
	if shared:
		requested = [name for name in requested if name != "address"]
	if not requested:
		return []
	return [f"-fsanitize={','.join(requested)}", "-fno-omit-frame-pointer"]


def compile_c(
	*,
	output: Path,
	sources: Iterable[Path],
	include_dirs: Iterable[Path] = (ROOT,),
	shared: bool = False,
) -> Path:
	flags = ["-std=c11", "-Wall", "-Wextra", "-Werror", "-g"]
	flags.extend(sanitizer_flags(shared=shared))
	if shared:
		flags.append("-shared")
		if sys.platform != "win32":
			flags.append("-fPIC")

	command = [host_compiler(), *flags]
	for include_dir in include_dirs:
		command.extend(["-I", str(include_dir)])
	command.extend(str(source) for source in sources)
	command.extend(["-o", str(output)])
	subprocess.run(command, check=True)
	return output


def shared_library_path(directory: Path, stem: str) -> Path:
	if sys.platform == "win32":
		return directory / f"{stem}.dll"
	if sys.platform == "darwin":
		return directory / f"lib{stem}.dylib"
	return directory / f"lib{stem}.so"


def host_runtime_environment() -> dict[str, str]:
	environment = os.environ.copy()
	environment.setdefault("ASAN_OPTIONS", "detect_leaks=0:halt_on_error=1")
	environment.setdefault("UBSAN_OPTIONS", "halt_on_error=1:print_stacktrace=1")
	return environment
