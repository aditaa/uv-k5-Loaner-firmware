import subprocess

import pytest

from tests.host_tools import ROOT, compile_c, host_runtime_environment


@pytest.fixture(scope="session")
def fake_platform_harness(tmp_path_factory):
	output = tmp_path_factory.mktemp("fake-platform") / "fake_platform_harness"
	return compile_c(
		output=output,
		sources=[
			ROOT / "tests" / "host" / "fake_platform_harness.c",
			ROOT / "tests" / "host" / "fake_platform.c",
		],
	)


def test_fake_platform_adapters(fake_platform_harness):
	subprocess.run(
		[str(fake_platform_harness)],
		check=True,
		env=host_runtime_environment(),
	)
