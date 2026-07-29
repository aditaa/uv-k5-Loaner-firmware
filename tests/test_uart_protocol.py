import struct
import subprocess
from binascii import crc_hqx
from itertools import cycle

import pytest

from tests.host_tools import ROOT, compile_c, host_runtime_environment


OBFUSCATION = bytes(
    [
        0x16,
        0x6C,
        0x14,
        0xE6,
        0x2E,
        0x91,
        0x0D,
        0x40,
        0x21,
        0x35,
        0xD5,
        0x40,
        0x13,
        0x03,
        0xE9,
        0x80,
    ]
)


def command(command_id, body=b"", header_size=None):
    if header_size is None:
        header_size = len(body)
    return struct.pack("<HH", command_id, header_size) + body


def read_command(offset=0, size=128, header_size=None):
    body = struct.pack("<HBBI", offset, size, 0, 0x6457396A)
    return command(0x051B, body, header_size)


def write_command(offset=0, data=b"\x00" * 128, declared_size=None, header_size=None):
    if declared_size is None:
        declared_size = len(data)
    body = struct.pack("<HBBI", offset, declared_size, 1, 0x6457396A) + data
    return command(0x051D, body, header_size)


def frame(payload, encrypted=True, corrupt_crc=False):
    crc = crc_hqx(payload, 0)
    if corrupt_crc:
        crc ^= 0x0001
    encoded = payload + struct.pack("<H", crc)
    if encrypted:
        encoded = bytes(value ^ key for value, key in zip(encoded, cycle(OBFUSCATION)))
    return b"\xAB\xCD" + struct.pack("<H", len(payload)) + encoded + b"\xDC\xBA"


@pytest.fixture(scope="session")
def uart_harness(tmp_path_factory):
    executable = tmp_path_factory.mktemp("uart_protocol") / "uart_protocol_harness"
    return compile_c(
        output=executable,
        sources=[ROOT / "tests" / "uart_protocol_harness.c", ROOT / "app" / "uart_protocol.c"],
    )


def validate(uart_harness, payload):
    result = subprocess.run(
        [str(uart_harness), "validate", payload.hex()],
        check=True,
        capture_output=True,
        text=True,
        env=host_runtime_environment(),
    )
    return result.stdout.strip() == "1"


def parse(uart_harness, packet, ring_size=256, start=0, encrypted=True):
    result = subprocess.run(
        [
            str(uart_harness),
            "parse",
            packet.hex(),
            str(ring_size),
            str(start),
            str(int(encrypted)),
        ],
        check=True,
        capture_output=True,
        text=True,
        env=host_runtime_environment(),
    )
    frame_result, next_index, command_size, next_encrypted, command_id = result.stdout.split()
    return {
        "result": int(frame_result),
        "next_index": int(next_index),
        "command_size": int(command_size),
        "encrypted": bool(int(next_encrypted)),
        "command_id": int(command_id, 16),
    }


@pytest.mark.parametrize(
    "payload",
    [
        command(0x0514, struct.pack("<I", 0x6457396A)),
        read_command(),
        write_command(),
        command(0x0527),
        command(0x0529),
        command(0x052D, b"\x00" * 16),
        command(0x052F, struct.pack("<I", 0x6457396A)),
        command(0x05DD),
    ],
)
def test_valid_command_shapes(uart_harness, payload):
    assert validate(uart_harness, payload)


@pytest.mark.parametrize(
    "payload",
    [
        b"\x1B\x05\x08",
        command(0x051B),
        command(0x051D),
        read_command(header_size=7),
        read_command(size=0),
        read_command(size=129),
        read_command(offset=0x1FC0, size=128),
        read_command(offset=0xFFF0, size=32),
        write_command(offset=1),
        write_command(data=b"\x00" * 7),
        write_command(data=b"\x00" * 136),
        write_command(data=b"\x00" * 8, declared_size=16),
        write_command(offset=0x1FF8, data=b"\x00" * 16),
        command(0x052F),
        command(0x05DD, b"\x00"),
        command(0xFFFF),
    ],
)
def test_malformed_and_out_of_range_commands_are_rejected(uart_harness, payload):
    assert not validate(uart_harness, payload)


def test_encrypted_frame_parses_across_ring_wrap(uart_harness):
    payload = read_command(offset=0x1F80)
    packet = frame(payload)

    parsed = parse(uart_harness, packet, ring_size=64, start=55)

    assert parsed == {
        "result": 2,
        "next_index": (55 + len(packet)) % 64,
        "command_size": len(payload),
        "encrypted": True,
        "command_id": 0x051B,
    }


def test_bad_crc_is_consumed_without_dispatch(uart_harness):
    packet = frame(read_command(), corrupt_crc=True)

    parsed = parse(uart_harness, packet)

    assert parsed["result"] == 1
    assert parsed["next_index"] == len(packet)
    assert parsed["command_size"] == 0


def test_truncated_frame_waits_for_remaining_bytes(uart_harness):
    packet = frame(write_command(data=b"\x00" * 8))[:-1]

    parsed = parse(uart_harness, packet)

    assert parsed["result"] == 0
    assert parsed["next_index"] == 0
    assert parsed["command_size"] == 0


def test_oversized_outer_frame_is_rejected(uart_harness):
    parsed = parse(uart_harness, b"\xAB\xCD\xFF\xFF")

    assert parsed["result"] == 1
    assert parsed["next_index"] == 1
    assert parsed["command_size"] == 0


def test_invalid_eeprom_frame_is_consumed_without_dispatch(uart_harness):
    packet = frame(write_command(offset=0x1FF8, data=b"\x00" * 16))

    parsed = parse(uart_harness, packet)

    assert parsed["result"] == 1
    assert parsed["next_index"] == len(packet)
    assert parsed["command_size"] == 0


@pytest.mark.parametrize(
    "payload",
    [
        command(0x052F),
        command(0x05DD, b"\x00"),
    ],
)
def test_malformed_state_changing_frames_cannot_dispatch(uart_harness, payload):
    parsed = parse(uart_harness, frame(payload))

    assert parsed["result"] == 1
    assert parsed["command_size"] == 0


def test_valid_plaintext_hello_changes_encryption_only_after_crc(uart_harness):
    hello = command(0x0514, struct.pack("<I", 0x6457396A))

    valid = parse(uart_harness, frame(hello, encrypted=False), encrypted=True)
    invalid = parse(
        uart_harness,
        frame(hello, encrypted=False, corrupt_crc=True),
        encrypted=True,
    )

    assert valid["result"] == 2
    assert valid["encrypted"] is False
    assert invalid["result"] == 1
    assert invalid["encrypted"] is True
