import ast
import subprocess
import sys
from binascii import crc_hqx
from itertools import cycle
from pathlib import Path


def _load_obfuscation():
    tree = ast.parse(Path("fw-pack.py").read_text())
    for node in tree.body:
        if isinstance(node, ast.Assign):
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id == "OBFUSCATION":
                values = []
                for elt in node.value.elts:
                    if isinstance(elt, ast.Constant):
                        values.append(elt.value)
                    else:
                        raise ValueError("Unexpected AST element in OBFUSCATION table")
                return values
    raise RuntimeError("OBFUSCATION table not found")


OBFUSCATION = _load_obfuscation()


def deobfuscate(payload: bytes) -> bytes:
    return bytes(a ^ b for a, b in zip(payload, cycle(OBFUSCATION)))


def run_fw_pack(input_path, version, output_path):
    subprocess.run(
        [sys.executable, "fw-pack.py", str(input_path), version, str(output_path)],
        check=True,
    )


def test_fw_pack_injects_version(tmp_path):
    plain = (b"\x01\x02\x03\x04" * 4096)  # 16 KiB test payload
    input_bin = tmp_path / "input.bin"
    packed_bin = tmp_path / "output.bin"
    input_bin.write_bytes(plain)

    run_fw_pack(input_bin, "LOANER01", packed_bin)

    data = packed_bin.read_bytes()
    assert len(data) == len(plain) + 16 + 2  # Version block inserted + CRC

    deobfuscated = deobfuscate(data[:-2])
    version_block = deobfuscated[0x2000:0x2010]
    assert version_block.startswith(b"*OEFW-")
    assert version_block[6:6 + len("LOANER01")] == b"LOANER01"
    assert version_block.endswith(b"\x00" * (16 - len("*OEFW-") - len("LOANER01")))

    # Verify CRC matches (xmodem polynomial)
    payload, crc_bytes = data[:-2], data[-2:]
    crc = crc_hqx(payload, 0x0000)
    assert crc_bytes == bytes([crc & 0xFF, (crc >> 8) & 0xFF])


def test_fw_pack_rejects_long_version(tmp_path):
    input_bin = tmp_path / "input.bin"
    input_bin.write_bytes(b"\x00" * 0x2100)
    packed_bin = tmp_path / "output.bin"

    result = subprocess.run(
        [sys.executable, "fw-pack.py", str(input_bin), "THIS_IS_TOO_LONG", str(packed_bin)],
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "Version suffix is too big" in result.stdout
    assert not packed_bin.exists()
