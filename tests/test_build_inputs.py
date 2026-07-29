import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ACTION_PIN = re.compile(
	r"uses:\s+[^@\s]+@(?P<sha>[0-9a-f]{40})\s+#\s+v[0-9]+\.[0-9]+\.[0-9]+\s*$"
)
EXACT_REQUIREMENT = re.compile(r"^[A-Za-z0-9_.-]+==[^=<>!~\s]+$")


def test_all_workflow_actions_are_immutable_and_documented():
	uses_lines = []
	for workflow in sorted((ROOT / ".github" / "workflows").glob("*.yaml")):
		for line_number, line in enumerate(workflow.read_text(encoding="utf-8").splitlines(), 1):
			if "uses:" not in line:
				continue
			uses_lines.append((workflow, line_number, line.strip()))
			assert ACTION_PIN.search(line), f"mutable or undocumented action at {workflow}:{line_number}"

	assert uses_lines


def test_python_ci_dependencies_are_exactly_pinned():
	lines = (ROOT / "ci" / "requirements-ci.txt").read_text(encoding="utf-8").splitlines()
	requirements = [line for line in lines if line and not line.startswith("#")]

	assert requirements
	assert all(EXACT_REQUIREMENT.fullmatch(requirement) for requirement in requirements)
	assert len({requirement.split("==", 1)[0].lower() for requirement in requirements}) == len(
		requirements
	)


def test_container_and_toolchain_inputs_are_pinned():
	dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
	checksum = (
		ROOT / "ci" / "gcc-arm-none-eabi-10.3-2021.10.sha256"
	).read_text(encoding="ascii")

	assert re.search(r"^FROM archlinux:base-devel@sha256:[0-9a-f]{64}$", dockerfile, re.MULTILINE)
	assert re.search(
		r"^ARG ARCH_REPOSITORY_DATE=[0-9]{4}/[0-9]{2}/[0-9]{2}$",
		dockerfile,
		re.MULTILINE,
	)
	assert "archlinux:latest" not in dockerfile
	assert "BUILD_CONTAINER_BASE=" in dockerfile
	assert 'BUILD_PACKAGE_SNAPSHOT="${ARCH_REPOSITORY_DATE}"' in dockerfile
	assert re.fullmatch(
		r"[0-9a-f]{64}  gcc-arm-none-eabi-10\.3-2021\.10-x86_64-linux\.tar\.bz2\n",
		checksum,
	)
	assert "sha256sum --check" in (ROOT / "ci" / "install-arm-toolchain.sh").read_text(
		encoding="utf-8"
	)


def test_docker_context_excludes_local_and_generated_state():
	patterns = set((ROOT / ".dockerignore").read_text(encoding="utf-8").splitlines())

	assert "/.git" in patterns
	assert "/compiled-firmware" in patterns
	assert "**/__pycache__" in patterns
	assert "/.docker-format.*" in patterns


def test_full_pipeline_requires_two_identical_builds():
	run_script = (ROOT / "ci" / "run.sh").read_text(encoding="utf-8")
	repro_script = (ROOT / "ci" / "check-reproducible-build.sh").read_text(encoding="utf-8")

	assert "check-reproducible-build.sh" in run_script
	assert repro_script.count("build_firmware") >= 3
	assert 'cmp "${FIRST_BUILD}/loaner-firmware.bin" loaner-firmware.bin' in repro_script
	assert (
		'cmp "${FIRST_BUILD}/loaner-firmware.packed.bin" loaner-firmware.packed.bin'
		in repro_script
	)


def test_ci_suffixes_and_chirp_source_do_not_drift():
	main_workflow = (ROOT / ".github" / "workflows" / "main.yaml").read_text(encoding="utf-8")
	codeql_workflow = (ROOT / ".github" / "workflows" / "codeql.yaml").read_text(
		encoding="utf-8"
	)

	assert "aditaa/chirp" not in main_workflow
	assert "loaner-firmware-whitelist" not in main_workflow
	assert "COMPAT_SUFFIX" not in main_workflow
	assert "REQUESTED_SUFFIX" not in main_workflow
	assert 'SUFFIX="CI${' not in main_workflow
	assert main_workflow.count("submodules: recursive") >= 2
	assert 'TARGET=loaner-firmware VERSION_SUFFIX="${VERSION_SUFFIX}"' in main_workflow
	assert "VERSION_SUFFIX: LNR" not in codeql_workflow
	assert "< VERSION_SUFFIX" in main_workflow
	assert "< VERSION_SUFFIX" in codeql_workflow


def test_release_workflow_uses_versioned_release_notes():
	release_workflow = (ROOT / ".github" / "workflows" / "release.yaml").read_text(
		encoding="utf-8"
	)

	assert 'VERSION_SUFFIX: ${{ steps.release.outputs.version_suffix }}' in release_workflow
	assert '--notes-file "docs/releases/${VERSION_SUFFIX}.md"' in release_workflow
	assert "--generate-notes" not in release_workflow
