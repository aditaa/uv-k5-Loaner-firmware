import shutil
import subprocess
import textwrap
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def frequency_policy_binary(tmp_path_factory):
    compiler = shutil.which("cc") or shutil.which("gcc")
    if compiler is None:
        pytest.skip("A host C compiler is required for the frequency policy test")

    build_dir = tmp_path_factory.mktemp("frequency-policy")
    harness = build_dir / "frequency_policy_harness.c"
    executable = build_dir / "frequency_policy_harness"
    harness.write_text(
        textwrap.dedent(
            """
            #include <stdint.h>
            #include <stdio.h>
            #include <stdlib.h>

            #include "frequencies.h"
            #include "misc.h"

            int main(int argc, char **argv)
            {
                FREQ_Config_t tx;
                VFO_Info_t vfo = {0};
                uint32_t frequency;
                uint8_t channel;

                if (argc != 3) {
                    return 2;
                }

                frequency = (uint32_t)strtoul(argv[1], NULL, 10);
                channel = (uint8_t)strtoul(argv[2], NULL, 10);
                tx.Frequency = frequency;
                vfo.pTX = &tx;
                vfo.CHANNEL_SAVE = channel;

                printf("%u %d\\n",
                       FREQUENCY_IsSupported(frequency),
                       FREQUENCY_Check(&vfo));
                return 0;
            }
            """
        ),
        encoding="utf-8",
    )
    subprocess.run(
        [
            compiler,
            "-std=c11",
            "-Wall",
            "-Werror",
            "-I",
            str(ROOT),
            str(ROOT / "frequencies.c"),
            str(harness),
            "-o",
            str(executable),
        ],
        check=True,
    )
    return executable


def run_policy(executable, frequency, channel=0):
    result = subprocess.run(
        [str(executable), str(frequency), str(channel)],
        check=True,
        capture_output=True,
        text=True,
    )
    supported, check_result = result.stdout.split()
    return supported == "1", int(check_result)


@pytest.mark.parametrize(
    ("frequency", "expected"),
    [
        (4_999_999, False),
        (5_000_000, True),
        (7_600_000, True),
        (7_600_001, False),
        (10_799_999, False),
        (10_800_000, True),
        (13_599_990, True),
        (13_600_000, True),
        (17_399_990, True),
        (17_400_000, True),
        (34_999_990, True),
        (35_000_000, True),
        (39_999_990, True),
        (40_000_000, True),
        (46_255_000, True),
        (46_755_000, True),
        (46_999_990, True),
        (47_000_000, True),
        (60_000_000, True),
        (60_000_001, False),
    ],
)
def test_supported_transmit_ranges(frequency_policy_binary, frequency, expected):
    supported, check_result = run_policy(frequency_policy_binary, frequency)

    assert supported is expected
    assert check_result == (0 if expected else -1)


def test_special_channels_remain_non_transmittable(frequency_policy_binary):
    supported, check_result = run_policy(
        frequency_policy_binary,
        46_255_000,
        channel=207,
    )

    assert supported is True
    assert check_result == -1
